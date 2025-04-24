from fpdf import FPDF, HTMLMixin

import csv
from django.http import HttpResponse
from datetime import datetime

import csv
from django.http import HttpResponse
from datetime import datetime
import os

from django.conf import settings

# PDF generation functions (unchanged from your original file)
def generate_course_pdf(reg_course, student, session, semester, confirmReg):
    class PDF(FPDF, HTMLMixin):
        def header(self):
            self.image("aconsa_logo.png", 10, 4, 20)
            self.set_font("helvetica", "B", 14)
            self.cell(179, 0, "ACHIEVERS COLLEGE OF NURSING SCIENCES, AKURE", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 10)
            self.cell(170, 7, "a subsidiary of", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 11)
            self.cell(170, 5, "ACHIEVERS UNIVERSITY, OWO", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 10)
            self.cell(170, 7, "www.achieversnursingcollege.edu.ng", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 11)
            self.cell(170, 5, "Course Registration", border=False, ln=1, align="C")
            self.ln(1)
            self.image("aconsa_logo.png", 170, 4, 23)

    pdf = PDF("P", "mm", "Letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.ln()

    pdf.set_font("times", "B", 6)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(129, 4, f"Printed on: {datetime.now()}")
    pdf.set_font("times", "B", 10)
    pdf.cell(0, 4, f" {confirmReg.session.year} || {confirmReg.semester.name.upper()} SEMESTER", ln=True)
    pdf.set_font("times", "B", 10)
    pdf.set_fill_color(118, 43, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(180, 7, f"   :. Students' Personal Information", ln=True, fill=True, align="L")
    pdf.set_font("times", "B", 7)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 7, f"FULL NAME:")
    pdf.cell(0, 7, f"{student.surname.upper()}, {student.otherNames.upper()}", ln=True)
    pdf.cell(60, 7, f"MATRIC NO / JAMB NO:")
    pdf.cell(0, 7, f"{student.matricNumber.upper()} [95753342EC]", ln=True)
    pdf.cell(60, 7, f"FACULTY / COLLEGE:")
    pdf.cell(0, 7, f"{student.college.name.upper()}", ln=True)
    pdf.cell(60, 7, f"PROGRAMME:")
    pdf.cell(0, 7, f"{student.programme.name.upper()}", ln=True)
    pdf.cell(60, 7, f"DEGREE:")
    pdf.cell(0, 7, f"{student.degree.upper()} {student.programme.name.upper()}", ln=True)
    pdf.cell(60, 7, f"EMAIL / PHONE NO:")
    pdf.cell(0, 7, f"{student.primaryEmail} || {student.studentPhoneNumber}", ln=True)
    pdf.cell(60, 7, f"LEVEL:")
    pdf.cell(0, 7, f"{confirmReg.level.name.upper()}")

    if student.passport:
        image_path = os.path.join(settings.MEDIA_ROOT, student.passport.name)
        if os.path.exists(image_path):
            pdf.image(image_path, 170, 50, 23)

    pdf.ln()
    pdf.set_font("Arial", "B", 6)
    pdf.set_text_color(0, 0, 0)
    unit = 0
    for co in reg_course:
        pdf.cell(25, 4, f"{co.course.courseCode.upper()}", border=1)
        pdf.cell(100, 4, f"{co.course.title.upper()}", border=1)
        pdf.cell(15, 4, f"{co.course.unit}", border=1)
        pdf.cell(30, 4, f"{co.course.status.upper()}", border=1)
        pdf.cell(15, 4, f"", border=1)
        pdf.ln()
        unit += co.course.unit

    pdf.cell(25, 4, f"", border=1)
    pdf.cell(100, 4, f"Total Registered Units", border=1)
    pdf.cell(15, 4, f"{unit}", border=1)
    pdf.cell(30, 4, f"", border=1)
    pdf.cell(15, 4, f"", border=1)
    pdf.ln()

    pdf.set_font("times", "", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, f"Key: C=Compulsory, E=Elective, R=Required", ln=True)
    pdf.ln(4)
    pdf.set_font("times", "", 7)
    pdf.cell(145, 7, f"Signature of Student: _____________________________________")
    pdf.cell(0, 7, f"Date: __________________________", ln=True)
    pdf.set_font("times", "B", 10)
    pdf.cell(180, 7, f"FOR OFFICIAL USE ONLY", align="C", ln=True)
    pdf.set_font("times", "B", 6)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(180, 2, f"I certify that the above named student has submitted four(4) copies of his/her first semester course registration form and he/she is qualified to register the above listed courses", align="C", ln=True)
    pdf.ln(6)
    pdf.set_font("times", "", 7)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(145, 7, f"Signature of Academic Advisor: ____________________________")
    pdf.cell(0, 7, f"Date: __________________________", ln=True)
    pdf.ln(6)
    pdf.cell(145, 7, f"Signature of H.O.D.: _____________________________________")
    pdf.cell(0, 7, f"Date: __________________________", ln=True)
    pdf.ln(6)
    pdf.cell(145, 7, f"Signature of PROVOST: _____________________________________")
    pdf.cell(0, 7, f"Date: __________________________", ln=True)
    pdf.ln(3)
    pdf.set_font("times", "B", 6)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(180, 2, f"Note:This form should be printed and returned to the Examination Officer at least Four weeks before the commencement of the examinations.", align="C", ln=True)
    pdf.cell(180, 2, f"No Candidate shall be allowed to write any examination in any course unless he/she has satisfied appropriate registration & finanacial regulations.", align="C")

    return pdf

def generate_pdf(reg_course, student, session, semester, confirmReg, gpa):
    class PDF(FPDF, HTMLMixin):
        def header(self):
            self.image("aconsa_logo.png", 10, 4, 20)
            self.set_font("helvetica", "B", 14)
            self.cell(179, 0, "ACHIEVERS COLLEGE OF NURSING SCIENCES, AKURE", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 10)
            self.cell(170, 7, "a subsidiary of", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 11)
            self.cell(170, 5, "ACHIEVERS UNIVERSITY, OWO", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 10)
            self.cell(170, 7, "www.achieversnursingcollege.edu.ng", border=False, ln=1, align="C")
            self.ln(1)
            self.set_font("helvetica", "B", 11)
            self.cell(170, 5, "Notification of Result", border=False, ln=1, align="C")
            self.ln(1)
            self.image("aconsa_logo.png", 170, 4, 23)

    pdf = PDF("P", "mm", "Letter")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.ln()

    pdf.set_font("times", "B", 6)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(129, 4, f"Printed on: {datetime.now()}")
    pdf.set_font("times", "B", 10)
    pdf.cell(0, 4, f" {confirmReg.session.year} || {confirmReg.semester.name.upper()} SEMESTER", ln=True)
    pdf.set_font("times", "B", 10)
    pdf.set_fill_color(118, 43, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(180, 7, f"   :. Students' Personal Information", ln=True, fill=True, align="L")
    pdf.set_font("times", "B", 7)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 7, f"FULL NAME:")
    pdf.cell(0, 7, f"{student.surname.upper()}, {student.otherNames.upper()}", ln=True)
    pdf.cell(60, 7, f"MATRIC NO / JAMB NO:")
    pdf.cell(0, 7, f"{student.matricNumber.upper()} [{student.jambNumber.upper()}]", ln=True)
    pdf.cell(60, 7, f"FACULTY / COLLEGE:")
    pdf.cell(0, 7, f"{student.college.name.upper()}", ln=True)
    pdf.cell(60, 7, f"PROGRAMME:")
    pdf.cell(0, 7, f"{student.programme.name.upper()}", ln=True)
    pdf.cell(60, 7, f"DEGREE:")
    pdf.cell(0, 7, f"{student.degree.upper()} {student.programme.name.upper()}", ln=True)
    pdf.cell(60, 7, f"EMAIL / PHONE NO:")
    pdf.cell(0, 7, f"{student.primaryEmail} || {student.studentPhoneNumber}", ln=True)
    pdf.cell(60, 7, f"LEVEL:")
    pdf.cell(0, 7, f"{confirmReg.level.name.upper()}")

    if student.passport:
        image_path = os.path.join(settings.MEDIA_ROOT, student.passport.name)
        if os.path.exists(image_path):
            pdf.image(image_path, 170, 58, 23)

    pdf.ln()
    pdf.set_font("Arial", "B", 6)
    pdf.set_text_color(0, 0, 0)
    unit = 0
    pdf.cell(25, 4, f"Code", border=1)
    pdf.cell(100, 4, f"Title", border=1)
    pdf.cell(15, 4, f"Unit", border=1)
    pdf.cell(15, 4, f"Score", border=1)
    pdf.cell(15, 4, f"Grade", border=1)
    pdf.ln()
    for co in reg_course:
        pdf.cell(25, 4, f"{co.registration.course.courseCode.upper()}", border=1)
        pdf.cell(100, 4, f"{co.registration.course.title.upper()}", border=1)
        pdf.cell(15, 4, f"{co.registration.course.unit}", border=1)
        pdf.cell(15, 4, f"{co.grade}", border=1)
        pdf.cell(15, 4, f"{co.grade_type.upper()}", border=1)
        pdf.ln()
        unit += co.registration.course.unit

    pdf.cell(25, 4, f"", border=1)
    pdf.cell(100, 4, f"Total Registered Units", border=1)
    pdf.cell(15, 4, f"{unit}", border=1)
    pdf.cell(15, 4, f"GPA", border=1)
    pdf.cell(15, 4, f"{gpa}", border=1)
    pdf.ln(16)

    pdf.set_font("times", "BU", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(20, 7, f"LEGEND:")

    pdf.ln(6)

    pdf.set_font("times", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 7, f"Class of Grade")

    pdf.ln(6)

    pdf.set_font("times", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 7, f"70-Above (A), 60-69 (B), 50-59 (C), 45-49 (D), below 50 for nursing and life sciences courses, and below 45 for other classes (F).")

    return pdf

# Helper functions for role checks