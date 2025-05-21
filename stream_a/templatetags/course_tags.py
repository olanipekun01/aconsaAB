from django import template
from stream_a.models import Result, Student, Course

register = template.Library()

@register.filter
def has_passed(course, student):
    if not isinstance(course, Course) or not isinstance(student, Student):
        return False
    return Result.objects.filter(
        registration__student=student,
        registration__course=course,
        grade_remark="passed"
    ).exists()