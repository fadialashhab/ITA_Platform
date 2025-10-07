from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Payment
from .serializers import (
    PaymentSerializer, PaymentListSerializer,
    PaymentCreateSerializer, PaymentUpdateSerializer,
    EnrollmentPaymentSummarySerializer, StudentPaymentSummarySerializer,
    PaymentStatisticsSerializer, OutstandingPaymentSerializer,
    RevenueReportSerializer, BulkPaymentSerializer,
    StudentPaymentSerializer
)
from .permissions import IsAdminOrFinance, IsAdminOrRegistrarOrFinance
from .filters import PaymentFilter


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments."""
    
    queryset = Payment.objects.select_related(
        'enrollment__student',
        'enrollment__course',
        'received_by'
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = [
        'receipt_number',
        'enrollment__student__username',
        'enrollment__student__email',
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'enrollment__course__title'
    ]
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date', '-created_at']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'list', 'retrieve']:
            permission_classes = [IsAdminOrRegistrarOrFinance]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrFinance]
        else:
            permission_classes = [IsAdminOrFinance]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return PaymentListSerializer
        elif self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentUpdateSerializer
        elif self.action == 'bulk_create':
            return BulkPaymentSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = Payment.objects.select_related(
            'enrollment__student',
            'enrollment__course',
            'received_by'
        )
        
        # Filter by student
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(enrollment__course_id=course_id)
        
        # Filter by enrollment
        enrollment_id = self.request.query_params.get('enrollment', None)
        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method', None)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get overall payment summary."""
        queryset = self.get_queryset()
        
        total_revenue = queryset.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        payment_count = queryset.count()
        
        # Average payment amount
        avg_payment = queryset.aggregate(
            avg=Avg('amount')
        )['avg'] or Decimal('0.00')
        
        # By payment method
        by_method = {}
        for method, _ in Payment.PAYMENT_METHOD_CHOICES:
            method_total = queryset.filter(
                payment_method=method
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            if method_total > 0:
                by_method[method] = float(method_total)
        
        return Response({
            'total_revenue': total_revenue,
            'payment_count': payment_count,
            'average_payment': avg_payment,
            'by_method': by_method
        })
    
    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """Get enrollments with outstanding payments."""
        from enrollments.models import Enrollment
        
        # Get all active enrollments
        enrollments = Enrollment.objects.filter(
            status__in=['IN_PROGRESS', 'COMPLETED']
        ).select_related('student', 'course')
        
        outstanding_list = []
        
        for enrollment in enrollments:
            total_paid = Payment.get_total_paid_for_enrollment(enrollment)
            outstanding = enrollment.course.price - total_paid
            
            if outstanding > 0:
                # Get last payment date
                last_payment = Payment.objects.filter(
                    enrollment=enrollment
                ).order_by('-payment_date').first()
                
                days_since_enrollment = (timezone.now().date() - enrollment.enrollment_date).days
                
                outstanding_list.append({
                    'enrollment_id': enrollment.id,
                    'student_id': enrollment.student.id,
                    'student_name': enrollment.student.get_full_name(),
                    'student_email': enrollment.student.email,
                    'student_phone': enrollment.student.phone_number,
                    'course_id': enrollment.course.id,
                    'course_title': enrollment.course.title,
                    'enrollment_date': enrollment.enrollment_date,
                    'course_price': enrollment.course.price,
                    'total_paid': total_paid,
                    'outstanding_balance': outstanding,
                    'last_payment_date': last_payment.payment_date if last_payment else None,
                    'days_since_enrollment': days_since_enrollment
                })
        
        # Sort by outstanding balance (highest first)
        outstanding_list.sort(key=lambda x: x['outstanding_balance'], reverse=True)
        
        # Paginate
        page = self.paginate_queryset(outstanding_list)
        if page is not None:
            serializer = OutstandingPaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OutstandingPaymentSerializer(outstanding_list, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Generate payment reports."""
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        period = request.query_params.get('period', 'month')  # day, week, month, year
        
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        else:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        queryset = Payment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
        )
        
        # Total revenue
        total_revenue = queryset.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        payment_count = queryset.count()
        
        # Average payment
        avg_payment = total_revenue / payment_count if payment_count > 0 else Decimal('0.00')
        
        # By payment method
        by_method = {}
        for method, _ in Payment.PAYMENT_METHOD_CHOICES:
            method_total = queryset.filter(
                payment_method=method
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            if method_total > 0:
                by_method[method] = float(method_total)
        
        # By course
        from courses.models import Course
        courses = Course.objects.filter(
            enrollments__payments__in=queryset
        ).annotate(
            revenue=Sum('enrollments__payments__amount')
        ).order_by('-revenue')[:10]
        
        by_course = [
            {
                'course_id': course.id,
                'course_title': course.title,
                'revenue': float(course.revenue)
            }
            for course in courses
        ]
        
        # Daily breakdown
        daily_breakdown = []
        current_date = start_date
        while current_date <= end_date:
            daily_total = queryset.filter(
                payment_date=current_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            daily_breakdown.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(daily_total)
            })
            current_date += timedelta(days=1)
        
        report_data = {
            'period': f"{start_date} to {end_date}",
            'total_revenue': float(total_revenue),
            'payment_count': payment_count,
            'average_payment': float(avg_payment),
            'by_method': by_method,
            'by_course': by_course,
            'daily_breakdown': daily_breakdown
        }
        
        serializer = RevenueReportSerializer(report_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive payment statistics."""
        # Total revenue (all time)
        total_revenue = Payment.objects.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        total_payments = Payment.objects.count()
        
        # Calculate total outstanding
        from enrollments.models import Enrollment
        all_enrollments = Enrollment.objects.filter(
            status__in=['IN_PROGRESS', 'COMPLETED']
        )
        
        total_outstanding = Decimal('0.00')
        for enrollment in all_enrollments:
            outstanding = Payment.get_outstanding_balance(enrollment)
            if outstanding > 0:
                total_outstanding += outstanding
        
        # Revenue this month
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        revenue_this_month = Payment.objects.filter(
            payment_date__gte=first_day_of_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Revenue this year
        first_day_of_year = today.replace(month=1, day=1)
        revenue_this_year = Payment.objects.filter(
            payment_date__gte=first_day_of_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Payments by method
        payments_by_method = {}
        for method, _ in Payment.PAYMENT_METHOD_CHOICES:
            method_total = Payment.objects.filter(
                payment_method=method
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            if method_total > 0:
                payments_by_method[method] = float(method_total)
        
        # Revenue by month (last 12 months)
        twelve_months_ago = today - timedelta(days=365)
        revenue_by_month = []
        
        for i in range(12):
            month_start = twelve_months_ago + timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            month_revenue = Payment.objects.filter(
                payment_date__gte=month_start,
                payment_date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            revenue_by_month.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(month_revenue)
            })
        
        # Top paying students
        from accounts.models import User
        students = User.objects.filter(
            role='STUDENT',
            enrollments__payments__isnull=False
        ).annotate(
            total_paid=Sum('enrollments__payments__amount')
        ).order_by('-total_paid')[:10]
        
        top_paying_students = [
            {
                'student_id': student.id,
                'student_name': student.get_full_name(),
                'total_paid': float(student.total_paid)
            }
            for student in students
        ]
        
        # Recent payments
        recent = Payment.objects.select_related(
            'enrollment__student',
            'enrollment__course'
        ).order_by('-payment_date', '-created_at')[:5]
        
        recent_payments = [
            {
                'id': p.id,
                'receipt_number': p.receipt_number,
                'student_name': p.get_student_name(),
                'course_title': p.get_course_title(),
                'amount': float(p.amount),
                'payment_date': p.payment_date,
                'payment_method': p.payment_method
            }
            for p in recent
        ]
        
        # Outstanding by student (top 10)
        outstanding_by_student = []
        students_with_outstanding = User.objects.filter(
            role='STUDENT',
            enrollments__status__in=['IN_PROGRESS', 'COMPLETED']
        ).distinct()
        
        for student in students_with_outstanding:
            student_outstanding = Decimal('0.00')
            for enrollment in student.enrollments.filter(status__in=['IN_PROGRESS', 'COMPLETED']):
                outstanding = Payment.get_outstanding_balance(enrollment)
                if outstanding > 0:
                    student_outstanding += outstanding
            
            if student_outstanding > 0:
                outstanding_by_student.append({
                    'student_id': student.id,
                    'student_name': student.get_full_name(),
                    'outstanding_balance': float(student_outstanding)
                })
        
        outstanding_by_student.sort(key=lambda x: x['outstanding_balance'], reverse=True)
        outstanding_by_student = outstanding_by_student[:10]
        
        data = {
            'total_revenue': float(total_revenue),
            'total_payments': total_payments,
            'total_outstanding': float(total_outstanding),
            'revenue_this_month': float(revenue_this_month),
            'revenue_this_year': float(revenue_this_year),
            'payments_by_method': payments_by_method,
            'revenue_by_month': revenue_by_month,
            'top_paying_students': top_paying_students,
            'recent_payments': recent_payments,
            'outstanding_by_student': outstanding_by_student
        }
        
        serializer = PaymentStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple payments at once."""
        serializer = BulkPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from enrollments.models import Enrollment
        
        payments_data = serializer.validated_data['payments']
        created_payments = []
        errors = []
        
        for i, payment_data in enumerate(payments_data):
            try:
                enrollment = Enrollment.objects.get(id=payment_data['enrollment_id'])
                
                payment = Payment.objects.create(
                    enrollment=enrollment,
                    amount=Decimal(str(payment_data['amount'])),
                    payment_method=payment_data['payment_method'],
                    payment_date=payment_data.get('payment_date', timezone.now().date()),
                    notes=payment_data.get('notes', ''),
                    received_by=request.user
                )
                created_payments.append(payment)
            except Exception as e:
                errors.append({
                    'index': i + 1,
                    'enrollment_id': payment_data.get('enrollment_id'),
                    'error': str(e)
                })
        
        response_data = {
            'message': f'Successfully created {len(created_payments)} payment(s).',
            'payments_created': len(created_payments),
            'payments': PaymentListSerializer(created_payments, many=True).data
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class StudentPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for students to view their own payments."""
    
    serializer_class = StudentPaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']
    
    def get_queryset(self):
        """Return only the current user's payments."""
        return Payment.objects.filter(
            enrollment__student=self.request.user
        ).select_related('enrollment__course')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get student's payment summary across all enrollments."""
        from enrollments.models import Enrollment
        
        # Get all student's enrollments
        enrollments = Enrollment.objects.filter(
            student=request.user
        ).select_related('course')
        
        total_paid = Decimal('0.00')
        total_outstanding = Decimal('0.00')
        fully_paid_count = 0
        partially_paid_count = 0
        unpaid_count = 0
        
        by_enrollment = []
        
        for enrollment in enrollments:
            course_price = enrollment.course.price
            payments = Payment.objects.filter(enrollment=enrollment)
            payments_total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            outstanding = course_price - payments_total
            
            total_paid += payments_total
            if outstanding > 0:
                total_outstanding += outstanding
            
            # Categorize
            if outstanding <= 0:
                fully_paid_count += 1
            elif payments_total > 0:
                partially_paid_count += 1
            else:
                unpaid_count += 1
            
            # Get last payment date
            last_payment = payments.order_by('-payment_date').first()
            
            by_enrollment.append({
                'enrollment_id': enrollment.id,
                'student_id': enrollment.student.id,
                'student_name': enrollment.student.get_full_name(),
                'student_email': enrollment.student.email,
                'course_id': enrollment.course.id,
                'course_title': enrollment.course.title,
                'course_price': course_price,
                'total_paid': payments_total,
                'outstanding_balance': max(outstanding, Decimal('0.00')),
                'is_fully_paid': outstanding <= 0,
                'payment_count': payments.count(),
                'last_payment_date': last_payment.payment_date if last_payment else None,
                'payments': PaymentListSerializer(payments, many=True).data
            })
        
        summary_data = {
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'fully_paid_enrollments': fully_paid_count,
            'partially_paid_enrollments': partially_paid_count,
            'unpaid_enrollments': unpaid_count,
            'by_enrollment': by_enrollment
        }
        
        serializer = StudentPaymentSummarySerializer(summary_data)
        return Response(serializer.data)