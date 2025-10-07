from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Payment
from enrollments.serializers import EnrollmentListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Full serializer for Payment model."""
    
    student_name = serializers.CharField(source='enrollment.student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='enrollment.student.email', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_price = serializers.DecimalField(
        source='enrollment.course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'enrollment', 'student_name', 'student_email',
            'course_title', 'course_price', 'amount', 'payment_date',
            'payment_method', 'receipt_number', 'received_by',
            'received_by_name', 'notes', 'remaining_balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'receipt_number', 'created_at', 'updated_at',
            'received_by', 'student_name', 'student_email',
            'course_title', 'course_price'
        ]
    
    def get_remaining_balance(self, obj):
        """Get remaining balance after this payment."""
        return obj.get_remaining_balance()


class PaymentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for payment listing."""
    
    student_name = serializers.CharField(source='enrollment.student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'receipt_number', 'student_name', 'course_title',
            'amount', 'payment_date', 'payment_method', 'received_by'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new payments."""
    
    class Meta:
        model = Payment
        fields = [
            'enrollment', 'amount', 'payment_date',
            'payment_method', 'notes'
        ]
    
    def validate_enrollment(self, value):
        """Validate enrollment status."""
        if value.status == 'CANCELLED':
            raise serializers.ValidationError(
                "Cannot record payment for a cancelled enrollment."
            )
        return value
    
    def validate_amount(self, value):
        """Validate payment amount is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )
        return value
    
    def validate_payment_date(self, value):
        """Validate payment date."""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Payment date cannot be in the future."
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        enrollment = attrs.get('enrollment')
        amount = attrs.get('amount')
        payment_date = attrs.get('payment_date')
        
        # Check if payment date is after enrollment date
        if payment_date < enrollment.enrollment_date:
            raise serializers.ValidationError({
                'payment_date': 'Payment date cannot be before enrollment date.'
            })
        
        # Check if total payments won't exceed course price
        existing_total = Payment.get_total_paid_for_enrollment(enrollment)
        new_total = existing_total + amount
        
        if new_total > enrollment.course.price:
            raise serializers.ValidationError({
                'amount': f'Total payments (${new_total}) would exceed course price (${enrollment.course.price}). Outstanding balance: ${enrollment.course.price - existing_total}'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create payment with received_by from request."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['received_by'] = request.user
        
        return Payment.objects.create(**validated_data)


class PaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payments."""
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'notes']


class EnrollmentPaymentSummarySerializer(serializers.Serializer):
    """Serializer for enrollment payment summary."""
    
    enrollment_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_email = serializers.CharField()
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    course_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_fully_paid = serializers.BooleanField()
    payment_count = serializers.IntegerField()
    last_payment_date = serializers.DateField(allow_null=True)
    payments = PaymentListSerializer(many=True)


class StudentPaymentSummarySerializer(serializers.Serializer):
    """Serializer for student's overall payment summary."""
    
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=10, decimal_places=2)
    fully_paid_enrollments = serializers.IntegerField()
    partially_paid_enrollments = serializers.IntegerField()
    unpaid_enrollments = serializers.IntegerField()
    by_enrollment = EnrollmentPaymentSummarySerializer(many=True)


class PaymentStatisticsSerializer(serializers.Serializer):
    """Serializer for payment statistics."""
    
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_payments = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_this_year = serializers.DecimalField(max_digits=12, decimal_places=2)
    payments_by_method = serializers.DictField()
    revenue_by_month = serializers.ListField()
    top_paying_students = serializers.ListField()
    recent_payments = serializers.ListField()
    outstanding_by_student = serializers.ListField()


class OutstandingPaymentSerializer(serializers.Serializer):
    """Serializer for enrollments with outstanding payments."""
    
    enrollment_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    student_email = serializers.CharField()
    student_phone = serializers.CharField()
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    enrollment_date = serializers.DateField()
    course_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_payment_date = serializers.DateField(allow_null=True)
    days_since_enrollment = serializers.IntegerField()


class RevenueReportSerializer(serializers.Serializer):
    """Serializer for revenue reports."""
    
    period = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_count = serializers.IntegerField()
    average_payment = serializers.DecimalField(max_digits=10, decimal_places=2)
    by_method = serializers.DictField()
    by_course = serializers.ListField()
    daily_breakdown = serializers.ListField()


class BulkPaymentSerializer(serializers.Serializer):
    """Serializer for recording multiple payments at once."""
    
    payments = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_payments(self, value):
        """Validate each payment in the list."""
        from enrollments.models import Enrollment
        
        for i, payment_data in enumerate(value):
            # Check required fields
            required_fields = ['enrollment_id', 'amount', 'payment_method']
            for field in required_fields:
                if field not in payment_data:
                    raise serializers.ValidationError(
                        f"Payment {i+1}: Missing required field '{field}'"
                    )
            
            # Validate enrollment exists
            try:
                enrollment = Enrollment.objects.get(id=payment_data['enrollment_id'])
            except Enrollment.DoesNotExist:
                raise serializers.ValidationError(
                    f"Payment {i+1}: Enrollment {payment_data['enrollment_id']} does not exist"
                )
            
            # Validate amount
            try:
                amount = Decimal(str(payment_data['amount']))
                if amount <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Payment {i+1}: Invalid amount"
                )
            
            # Check if total won't exceed course price
            existing_total = Payment.get_total_paid_for_enrollment(enrollment)
            if existing_total + amount > enrollment.course.price:
                raise serializers.ValidationError(
                    f"Payment {i+1}: Total would exceed course price"
                )
        
        return value


class StudentPaymentSerializer(serializers.ModelSerializer):
    """Serializer for students viewing their own payments."""
    
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_price = serializers.DecimalField(
        source='enrollment.course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'receipt_number', 'course_title', 'course_price',
            'amount', 'payment_date', 'payment_method',
            'remaining_balance', 'notes', 'created_at'
        ]
    
    def get_remaining_balance(self, obj):
        """Get remaining balance after this payment."""
        return obj.get_remaining_balance()