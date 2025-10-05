# courses app
from rest_framework import serializers
from .models import Category, Course


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    active_courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'is_active',
            'active_courses_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_courses_count(self, obj):
        """Return count of active courses in this category."""
        return obj.get_active_courses_count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for category listing."""
    
    class Meta:
        model = Category
        fields = ['id', 'name']


class PrerequisiteCourseSerializer(serializers.ModelSerializer):
    """Simplified serializer for prerequisite courses."""
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'level']


class CourseSerializer(serializers.ModelSerializer):
    """Full serializer for Course model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_detail = CategoryListSerializer(source='category', read_only=True)
    prerequisites_detail = PrerequisiteCourseSerializer(
        source='prerequisites',
        many=True,
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    # Statistics
    enrollment_count = serializers.SerializerMethodField()
    active_enrollment_count = serializers.SerializerMethodField()
    completion_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'duration', 'price',
            'level', 'category', 'category_name', 'category_detail',
            'prerequisites', 'prerequisites_detail',
            'is_active', 'created_by', 'created_by_name',
            'enrollment_count', 'active_enrollment_count',
            'completion_count', 'completion_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'enrollment_count', 'active_enrollment_count',
            'completion_count', 'completion_rate'
        ]
    
    def get_enrollment_count(self, obj):
        """Return total enrollment count."""
        return obj.get_enrollment_count()
    
    def get_active_enrollment_count(self, obj):
        """Return active enrollment count."""
        return obj.get_active_enrollment_count()
    
    def get_completion_count(self, obj):
        """Return completion count."""
        return obj.get_completion_count()
    
    def get_completion_rate(self, obj):
        """Return completion rate percentage."""
        return obj.get_completion_rate()
    
    def validate_prerequisites(self, value):
        """Validate prerequisites to prevent circular dependencies."""
        instance = self.instance
        if instance:
            # Check for circular dependencies
            for prereq in value:
                if prereq.id == instance.id:
                    raise serializers.ValidationError(
                        "A course cannot be its own prerequisite."
                    )
                # Check if this course is already a prerequisite of the prereq
                if instance.is_prerequisite_for(prereq):
                    raise serializers.ValidationError(
                        f"Circular dependency: '{prereq.title}' already has "
                        f"'{instance.title}' as a prerequisite."
                    )
        return value
    
    def validate_price(self, value):
        """Validate price is positive."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_duration(self, value):
        """Validate duration is positive."""
        if value < 1:
            raise serializers.ValidationError("Duration must be at least 1 hour.")
        return value


class CourseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for course listing."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    prerequisite_count = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'level', 'duration', 'price',
            'category', 'category_name', 'prerequisite_count',
            'enrollment_count', 'is_active', 'created_at'
        ]
    
    def get_prerequisite_count(self, obj):
        """Return number of prerequisites."""
        return obj.prerequisites.count()
    
    def get_enrollment_count(self, obj):
        """Return enrollment count."""
        return obj.get_enrollment_count()


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating courses."""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'duration', 'price',
            'level', 'category', 'prerequisites', 'is_active'
        ]
    
    def validate_prerequisites(self, value):
        """Validate prerequisites."""
        instance = self.instance
        if instance:
            for prereq in value:
                if prereq.id == instance.id:
                    raise serializers.ValidationError(
                        "A course cannot be its own prerequisite."
                    )
                if instance.is_prerequisite_for(prereq):
                    raise serializers.ValidationError(
                        f"Circular dependency detected with '{prereq.title}'."
                    )
        return value
    
    def create(self, validated_data):
        """Create course with prerequisites."""
        prerequisites = validated_data.pop('prerequisites', [])
        course = Course.objects.create(**validated_data)
        if prerequisites:
            course.prerequisites.set(prerequisites)
        return course
    
    def update(self, instance, validated_data):
        """Update course with prerequisites."""
        prerequisites = validated_data.pop('prerequisites', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if prerequisites is not None:
            instance.prerequisites.set(prerequisites)
        
        return instance


class PublicCourseSerializer(serializers.ModelSerializer):
    """Public-facing serializer for course catalog."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    prerequisites_detail = PrerequisiteCourseSerializer(
        source='prerequisites',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'duration', 'price',
            'level', 'category_name', 'prerequisites_detail'
        ]


class CourseStatisticsSerializer(serializers.Serializer):
    """Serializer for course statistics."""
    
    total_courses = serializers.IntegerField()
    active_courses = serializers.IntegerField()
    inactive_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    courses_by_level = serializers.DictField()
    courses_by_category = serializers.DictField()
    avg_completion_rate = serializers.FloatField()
    top_enrolled_courses = serializers.ListField()