# Script to generate fake_data/company_policy.pdf
# Run once: python generate_policy_pdf.py
from fpdf import FPDF

class PolicyPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'KARM Corp - Confidential HR Policy Document', align='C')
        self.ln(5)
        self.set_draw_color(0, 102, 204)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 74, 153)
        self.cell(0, 12, title)
        self.ln(10)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(51, 51, 51)
        self.cell(0, 10, title)
        self.ln(8)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 6, text)
        self.ln(4)

pdf = PolicyPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ===== TITLE PAGE =====
pdf.add_page()
pdf.ln(40)
pdf.set_font('Helvetica', 'B', 28)
pdf.set_text_color(0, 74, 153)
pdf.cell(0, 15, 'KARM Corp', align='C')
pdf.ln(15)
pdf.set_font('Helvetica', 'B', 20)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 12, 'Employee Handbook &', align='C')
pdf.ln(12)
pdf.cell(0, 12, 'HR Policy Document', align='C')
pdf.ln(20)
pdf.set_font('Helvetica', '', 12)
pdf.set_text_color(120, 120, 120)
pdf.cell(0, 8, 'Version 3.2 | Effective: January 1, 2025', align='C')
pdf.ln(8)
pdf.cell(0, 8, 'Human Resources Department', align='C')
pdf.ln(8)
pdf.cell(0, 8, 'Approved by: Meera Joshi, Head of HR', align='C')
pdf.ln(25)
pdf.set_font('Helvetica', 'I', 10)
pdf.cell(0, 8, 'This document is confidential and for KARM Corp employees only.', align='C')

# ===== TABLE OF CONTENTS =====
pdf.add_page()
pdf.chapter_title('Table of Contents')
toc = [
    ('1. Leave Policy', '3'),
    ('   1.1 Earned Leave', '3'),
    ('   1.2 Sick Leave', '3'),
    ('   1.3 Casual Leave', '3'),
    ('   1.4 Maternity & Paternity Leave', '4'),
    ('   1.5 Bereavement Leave', '4'),
    ('2. Work From Home Policy', '4'),
    ('   2.1 Eligibility', '4'),
    ('   2.2 WFH Schedule', '5'),
    ('   2.3 Equipment & Internet', '5'),
    ('   2.4 Availability Requirements', '5'),
    ('3. Maternity & Parental Benefits', '5'),
    ('   3.1 Maternity Leave Duration', '5'),
    ('   3.2 Paternity Leave', '6'),
    ('   3.3 Adoption Leave', '6'),
    ('   3.4 Childcare Support', '6'),
    ('4. Employee Perks & Benefits', '6'),
    ('   4.1 Health Insurance', '6'),
    ('   4.2 Learning & Development', '7'),
    ('   4.3 Wellness Program', '7'),
    ('   4.4 Employee Referral Bonus', '7'),
    ('5. Code of Conduct', '7'),
    ('   5.1 Anti-Harassment Policy', '8'),
    ('   5.2 Dress Code', '8'),
    ('   5.3 Conflict of Interest', '8'),
]
pdf.set_font('Helvetica', '', 11)
for item, page in toc:
    pdf.set_text_color(60, 60, 60)
    pdf.cell(160, 7, item)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 7, page, align='R')
    pdf.ln(7)

# ===== SECTION 1: LEAVE POLICY =====
pdf.add_page()
pdf.chapter_title('1. Leave Policy')
pdf.body_text(
    'KARM Corp recognizes the importance of work-life balance. All regular '
    'full-time employees are entitled to the following leave benefits from '
    'their date of joining. Leave must be applied for through the KARM HR '
    'Portal at least 3 working days in advance for planned leave, except in '
    'cases of emergency.'
)

pdf.section_title('1.1 Earned Leave (Privilege Leave)')
pdf.body_text(
    'Every employee earns 18 days of Earned Leave (EL) per calendar year, '
    'credited at the rate of 1.5 days per month. Earned Leave can be '
    'accumulated up to a maximum of 45 days. Any leave beyond 45 days will '
    'lapse at the end of the calendar year. Earned Leave can be encashed at '
    'the time of separation at the employee\'s last drawn basic salary. A '
    'minimum of 3 consecutive earned leave days must be taken at least once '
    'per year to encourage rest and recovery.'
)

pdf.section_title('1.2 Sick Leave')
pdf.body_text(
    'Employees are entitled to 12 days of Sick Leave per calendar year. Sick '
    'leave cannot be carried forward to the next year and will lapse on '
    'December 31st. For sick leave exceeding 3 consecutive days, a medical '
    'certificate from a registered medical practitioner must be submitted to '
    'the HR department within 3 days of resuming work. Failure to submit '
    'documentation may result in the leave being classified as Loss of Pay.'
)

pdf.section_title('1.3 Casual Leave')
pdf.body_text(
    'All employees receive 8 days of Casual Leave per calendar year. Casual '
    'Leave cannot be taken for more than 3 consecutive days at a time. Casual '
    'Leave cannot be combined with Earned Leave or Sick Leave. Casual Leave '
    'cannot be carried forward and will lapse at year-end. Employees must '
    'notify their reporting manager at least 24 hours before taking casual '
    'leave, except in genuine emergencies.'
)

pdf.section_title('1.4 Maternity & Paternity Leave')
pdf.body_text(
    'Female employees who have worked at KARM Corp for at least 80 days in '
    'the 12 months preceding the expected date of delivery are entitled to '
    '26 weeks (182 days) of paid Maternity Leave as per the Maternity Benefit '
    '(Amendment) Act, 2017. For employees with two or more surviving children, '
    'the entitlement is 12 weeks (84 days). During maternity leave, the '
    'employee will receive full salary and all existing benefits will continue.'
)
pdf.body_text(
    'Male employees are entitled to 15 days of paid Paternity Leave, to be '
    'taken within 6 months of the child\'s birth. Paternity leave can be taken '
    'in a single stretch or split into two blocks of minimum 5 days each.'
)

pdf.section_title('1.5 Bereavement Leave')
pdf.body_text(
    'In the unfortunate event of the death of an immediate family member '
    '(spouse, child, parent, sibling, or parent-in-law), employees are '
    'granted 5 days of paid Bereavement Leave. This leave must be taken '
    'within 30 days of the event. Additional unpaid leave may be granted '
    'at the manager\'s discretion.'
)

# ===== SECTION 2: WORK FROM HOME =====
pdf.add_page()
pdf.chapter_title('2. Work From Home Policy')
pdf.body_text(
    'KARM Corp supports flexible work arrangements to help employees maintain '
    'productivity while managing personal responsibilities. The Work From Home '
    '(WFH) policy applies to all roles that can be performed remotely as '
    'determined by the department head.'
)

pdf.section_title('2.1 Eligibility')
pdf.body_text(
    'All full-time employees who have completed their probation period '
    '(typically 6 months) are eligible for the WFH program. Employees on '
    'Performance Improvement Plans (PIP) are not eligible for WFH until the '
    'PIP period is successfully completed. Contract employees and interns may '
    'be granted WFH privileges on a case-by-case basis with explicit approval '
    'from their department head and HR.'
)

pdf.section_title('2.2 WFH Schedule')
pdf.body_text(
    'Employees may work from home for up to 3 days per week (Monday through '
    'Friday). The specific WFH days must be agreed upon with the reporting '
    'manager and should remain consistent each week to ensure team '
    'coordination. Wednesdays are designated as mandatory in-office '
    'collaboration days for all teams. During peak business periods '
    '(quarter-end, annual planning, client visits), WFH may be temporarily '
    'restricted with at least one week\'s notice.'
)

pdf.section_title('2.3 Equipment & Internet Allowance')
pdf.body_text(
    'KARM Corp provides a one-time WFH setup allowance of Rs. 15,000 for '
    'purchasing a monitor, keyboard, mouse, or ergonomic chair. A monthly '
    'internet reimbursement of Rs. 1,500 is provided upon submission of the '
    'internet bill. All employees are provided with a company laptop. '
    'Personal devices should not be used to access company code repositories '
    'or customer data. VPN must be used at all times when working remotely.'
)

pdf.section_title('2.4 Availability & Communication')
pdf.body_text(
    'Employees working from home must be available on Slack and email during '
    'core working hours: 10:00 AM to 6:00 PM IST. Camera must be turned on '
    'during team meetings and client calls. Response time to messages should '
    'not exceed 30 minutes during core hours. Employees must update their '
    'Slack status to reflect WFH days.'
)

# ===== SECTION 3: MATERNITY & PARENTAL =====
pdf.add_page()
pdf.chapter_title('3. Maternity & Parental Benefits')
pdf.body_text(
    'KARM Corp is committed to supporting employees through major life events. '
    'Our parental benefits go beyond statutory requirements to ensure that new '
    'parents feel supported and valued.'
)

pdf.section_title('3.1 Maternity Leave Duration & Benefits')
pdf.body_text(
    'As detailed in Section 1.4, eligible female employees receive 26 weeks '
    'of fully paid maternity leave. Additionally, KARM Corp offers:\n'
    '- Pre-natal medical expense coverage up to Rs. 50,000\n'
    '- Flexible return-to-work program at 60% capacity for the first month\n'
    '- Reserved parking spot for pregnant employees from the 6th month\n'
    '- Access to a dedicated mother\'s room at all office locations\n'
    '- Option to extend maternity leave by 4 additional unpaid weeks'
)

pdf.section_title('3.2 Paternity Leave & Benefits')
pdf.body_text(
    'Male employees receive 15 days of paid paternity leave. KARM Corp also '
    'provides:\n'
    '- Flexible work hours for 3 months after the child\'s birth\n'
    '- One-time childcare kit allowance of Rs. 10,000\n'
    '- Access to parental counseling through the Employee Assistance Program'
)

pdf.section_title('3.3 Adoption Leave')
pdf.body_text(
    'Employees who legally adopt a child under the age of three are entitled '
    'to 12 weeks of paid Adoption Leave. The same benefits as maternity or '
    'paternity leave apply. Documentation including the adoption order from '
    'the court must be submitted to HR.'
)

pdf.section_title('3.4 Childcare Support')
pdf.body_text(
    'KARM Corp provides a monthly childcare reimbursement of Rs. 5,000 per '
    'child (maximum 2 children) for employees with children under the age of '
    '6. This covers daycare, creche, or nanny expenses. Employees at our '
    'Bangalore and Mumbai offices have access to an on-site creche facility '
    'at subsidized rates.'
)

# ===== SECTION 4: PERKS =====
pdf.add_page()
pdf.chapter_title('4. Employee Perks & Benefits')

pdf.section_title('4.1 Health Insurance')
pdf.body_text(
    'All employees and their immediate dependents (spouse, up to 2 children, '
    'and parents) are covered under the KARM Corp Group Health Insurance:\n'
    '- Sum insured: Rs. 5,00,000 per family per year\n'
    '- Covers hospitalization, day-care procedures, pre/post hospitalization\n'
    '- Maternity coverage included (up to Rs. 75,000)\n'
    '- Pre-existing disease coverage after 2 years of enrollment\n'
    '- Dental coverage up to Rs. 15,000 per year\n'
    '- Mental health coverage including 12 therapy sessions per year'
)

pdf.section_title('4.2 Learning & Development')
pdf.body_text(
    'KARM Corp invests in employee growth through:\n'
    '- Annual learning budget of Rs. 30,000 per employee\n'
    '- Free access to Udemy Business, LinkedIn Learning, and Coursera\n'
    '- Internal mentorship program pairing junior and senior employees\n'
    '- Quarterly Innovation Days for passion projects\n'
    '- Full sponsorship for professional certifications (AWS, PMP, SHRM)\n'
    '- Study leave of up to 5 days per year for exam preparation'
)

pdf.section_title('4.3 Wellness Program')
pdf.body_text(
    'Employee wellness is a priority at KARM Corp:\n'
    '- Free gym membership or Rs. 2,000/month fitness reimbursement\n'
    '- Annual health checkup for all employees and spouse\n'
    '- Quarterly wellness workshops on stress, nutrition, finance\n'
    '- Employee Assistance Program (EAP) with 6 free counseling sessions\n'
    '- Meditation room available at all office locations\n'
    '- No Meeting Fridays after 2 PM to promote focused work time'
)

pdf.section_title('4.4 Employee Referral Program')
pdf.body_text(
    'Employees who refer candidates that are successfully hired receive:\n'
    '- Junior roles (0-3 years): Rs. 25,000\n'
    '- Mid-level roles (3-7 years): Rs. 50,000\n'
    '- Senior roles (7+ years): Rs. 1,00,000\n'
    '- Leadership roles (Director+): Rs. 2,00,000\n'
    'Bonus is paid in two installments: 50% upon joining and 50% after '
    'the referred employee completes 6 months.'
)

# ===== SECTION 5: CODE OF CONDUCT =====
pdf.add_page()
pdf.chapter_title('5. Code of Conduct')
pdf.body_text(
    'All KARM Corp employees are expected to maintain the highest standards '
    'of professional and ethical behavior. The following policies apply to '
    'all employees, contractors, and interns.'
)

pdf.section_title('5.1 Anti-Harassment & Anti-Discrimination Policy')
pdf.body_text(
    'KARM Corp has zero tolerance for harassment of any kind, including:\n'
    '- Sexual harassment as defined under the POSH Act, 2013\n'
    '- Discrimination based on gender, caste, religion, age, disability, '
    'sexual orientation, or regional origin\n'
    '- Bullying, intimidation, or creating a hostile work environment\n'
    '- Microaggressions and unconscious bias in workplace interactions\n\n'
    'All complaints should be directed to the Internal Complaints Committee '
    '(ICC) via email at icc@karmcorp.com or through the anonymous reporting '
    'portal. The ICC will investigate all complaints within 10 working days '
    'and maintain strict confidentiality. Retaliation against anyone filing '
    'a complaint is a terminable offense.'
)

pdf.section_title('5.2 Dress Code')
pdf.body_text(
    'KARM Corp follows a smart casual dress code:\n'
    '- Business formals required for client meetings and external events\n'
    '- Casual Fridays allow jeans and t-shirts (no shorts or flip-flops)\n'
    '- Company branded apparel for conferences (available from admin)\n'
    '- Safety gear mandatory in server room and lab areas'
)

pdf.section_title('5.3 Conflict of Interest')
pdf.body_text(
    'Employees must disclose any relationships that could create a conflict '
    'of interest, including:\n'
    '- Employment with or consulting for a competitor\n'
    '- Financial interest in a vendor or client company\n'
    '- Supervising or being supervised by a family member\n'
    '- Accepting gifts valued above Rs. 2,000 from vendors or clients\n\n'
    'Disclosures must be made in writing to HR within 30 days. Failure to '
    'disclose a known conflict may result in disciplinary action up to and '
    'including termination.'
)

pdf.body_text(
    'For questions about any policy in this document, please contact the HR '
    'department at hr@karmcorp.com or visit the HR Help Desk on the 3rd '
    'floor of any KARM Corp office.'
)

# Save
pdf.output('fake_data/company_policy.pdf')
print("SUCCESS: company_policy.pdf generated!")
