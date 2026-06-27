import os
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(patient_dict, risk_score, risk_category, risk_drivers, recommendations, 
                        simulator_projections=None, priority_areas=None, output_path="health_report.pdf", exec_summary=None):
    """
    Generate a professional clinical health screening report using ReportLab.
    Includes Patient Summary, Benchmarks, Simulator Projections, Priority Areas, and Date.
    """
    # Initialize document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=45
    )
    
    story = []
    
    # Core Palette
    PRIMARY_COLOR = colors.HexColor("#0D5C75")   # Deep Healthcare Teal
    SECONDARY_COLOR = colors.HexColor("#1A936F") # Green Accent
    TEXT_DARK = colors.HexColor("#2C3E50")       # Dark Charcoal for text
    BACKGROUND_LIGHT = colors.HexColor("#F4F7F6")# Light grey background
    BORDER_COLOR = colors.HexColor("#BDC3C7")    # Neutral border
    
    # Assign color tag for risk
    if risk_category == 'High Risk':
        RISK_TAG_COLOR = colors.HexColor("#C0392B") # Muted Red
    elif risk_category == 'Moderate Risk':
        RISK_TAG_COLOR = colors.HexColor("#D35400") # Muted Orange
    else:
        RISK_TAG_COLOR = colors.HexColor("#27AE60") # Muted Green
        
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY_COLOR,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor("#7F8C8D"),
        spaceAfter=12
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=TEXT_DARK,
        leading=13
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    risk_label_style = ParagraphStyle(
        'RiskLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.white,
        alignment=1 # Centered
    )
    
    # Header Banner/Line
    story.append(Paragraph("CLINICAL RISK ASSESSMENT REPORT", title_style))
    story.append(Paragraph("Cardiometabolic Risk Intelligence Platform • Screening Summary", subtitle_style))
    story.append(Spacer(1, 5))
    
    # Assessment Date
    assess_date = patient_dict.get('timestamp')
    if not assess_date:
        assess_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
    # Risk Summary Callout Box (Table)
    risk_summary_data = [
        [
            Paragraph("<b>Patient Name:</b>", body_style),
            Paragraph(patient_dict.get('name', 'Anonymous'), bold_body_style),
            Paragraph("<b>Assessment Date:</b>", body_style),
            Paragraph(str(assess_date), body_style)
        ],
        [
            Paragraph("<b>Risk Category:</b>", body_style),
            Table([[Paragraph(risk_category.upper(), risk_label_style)]], 
                  colWidths=[120], 
                  rowHeights=[20], 
                  style=TableStyle([
                      ('BACKGROUND', (0,0), (-1,-1), RISK_TAG_COLOR),
                      ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                      ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                      ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                      ('TOPPADDING', (0,0), (-1,-1), 0),
                  ])),
            Paragraph("<b>Risk Score:</b>", body_style),
            Paragraph(f"<b>{risk_score}%</b>", bold_body_style)
        ]
    ]
    
    summary_table = Table(risk_summary_data, colWidths=[90, doc.width/2 - 90, 110, doc.width/2 - 110])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BACKGROUND_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 10))
    
    if exec_summary:
        exec_summary_style = ParagraphStyle(
            'ExecSummaryStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9.5,
            textColor=TEXT_DARK,
            leading=14,
            spaceAfter=10
        )
        story.append(Paragraph(f"<b>Executive Clinical Summary:</b> {exec_summary}", exec_summary_style))
        story.append(Spacer(1, 5))
    
    # Priority Focus Areas Section
    if priority_areas:
        story.append(Paragraph("🎯 Clinical Priority Focus Areas", section_heading))
        priority_bullets = []
        for p in priority_areas:
            priority_bullets.append(Paragraph(p, bold_body_style))
        
        priority_table = Table([[b] for b in priority_bullets], colWidths=[doc.width])
        priority_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#FDE68A")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(priority_table)
        story.append(Spacer(1, 10))
        
    # 1. Patient Health Benchmarks
    story.append(Paragraph("1. Recorded Vitals & Health Benchmarks", section_heading))
    
    bmi = patient_dict.get('bmi', 22.0)
    glucose = patient_dict.get('glucose', 90)
    sys_bp = patient_dict.get('systolic_bp', 120)
    dia_bp = patient_dict.get('diastolic_bp', 80)
    cholesterol = patient_dict.get('cholesterol', 180)
    
    # BMI Benchmark status
    if 18.5 <= bmi <= 24.9:
        bmi_status = "Optimal"
    elif 25.0 <= bmi <= 29.9 or 17.0 <= bmi < 18.5:
        bmi_status = "Needs Improvement"
    else:
        bmi_status = "High Risk"
        
    # Glucose status
    if glucose < 100:
        glu_status = "Normal"
    elif 100 <= glucose <= 125:
        glu_status = "Pre-Diabetic"
    else:
        glu_status = "Diabetic"
        
    # BP status
    if sys_bp < 120 and dia_bp < 80:
        bp_status = "Optimal"
    elif sys_bp < 130 and dia_bp < 80:
        bp_status = "Elevated"
    else:
        bp_status = "Hypertension"
        
    # Cholesterol status
    if cholesterol < 200:
        chol_status = "Normal"
    elif 200 <= cholesterol <= 239:
        chol_status = "Borderline High"
    else:
        chol_status = "High Cholesterol"
        
    benchmarks_data = [
        [
            Paragraph("<b>Metric</b>", bold_body_style), 
            Paragraph("<b>Current Value</b>", bold_body_style),
            Paragraph("<b>Clinical Ideal Range</b>", bold_body_style),
            Paragraph("<b>Benchmark Status</b>", bold_body_style)
        ],
        [
            Paragraph("BMI (Body Mass Index)", body_style), 
            Paragraph(f"{bmi:.1f}", body_style),
            Paragraph("18.5 – 24.9", body_style),
            Paragraph(bmi_status, bold_body_style)
        ],
        [
            Paragraph("Fasting Blood Glucose", body_style), 
            Paragraph(f"{glucose:.0f} mg/dL", body_style),
            Paragraph("&lt; 100 mg/dL", body_style),
            Paragraph(glu_status, bold_body_style)
        ],
        [
            Paragraph("Blood Pressure", body_style), 
            Paragraph(f"{sys_bp:.0f}/{dia_bp:.0f} mmHg", body_style),
            Paragraph("120/80 mmHg", body_style),
            Paragraph(bp_status, bold_body_style)
        ],
        [
            Paragraph("Total Cholesterol", body_style), 
            Paragraph(f"{cholesterol:.0f} mg/dL", body_style),
            Paragraph("&lt; 200 mg/dL", body_style),
            Paragraph(chol_status, bold_body_style)
        ]
    ]
    
    benchmarks_table = Table(benchmarks_data, colWidths=[160, 110, 130, doc.width - 400])
    benchmarks_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E6ECEF")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(benchmarks_table)
    story.append(Spacer(1, 10))
    
    # 2. Risk Driver Analysis
    story.append(Paragraph("2. Explainable AI Risk Drivers (Local Feature Contribution)", section_heading))
    drivers_intro = (
        "Perturbation SHAP analysis calculates the individual contribution of each metabolic parameter "
        "to the patient's overall cardiometabolic risk score. The top clinical drivers are listed below:"
    )
    story.append(Paragraph(drivers_intro, body_style))
    story.append(Spacer(1, 4))
    
    drivers_list = []
    for d in risk_drivers:
        drivers_list.append([
            Paragraph(f"• <b>{d['label']}</b>", body_style),
            Paragraph(f"Attributed Value: <b>{d['value']}</b>", body_style),
            Paragraph(f"Risk Multiplier Contribution: <b>+{d['contribution']:.1f}%</b>", bold_body_style)
        ])
        
    if not drivers_list:
        drivers_list.append([
            Paragraph("• No significant risk drivers identified. Patient metrics are within optimal baselines.", body_style),
            Paragraph("", body_style),
            Paragraph("", body_style)
        ])
        
    drivers_table = Table(drivers_list, colWidths=[200, 150, doc.width - 350])
    drivers_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(drivers_table)
    story.append(Spacer(1, 10))
    
    # 3. Projected Priority Intervention Plan Targets
    if simulator_projections:
        story.append(Paragraph("3. Projected Priority Intervention Plan Targets", section_heading))
        story.append(Paragraph("The priority intervention plan outlines the primary metabolic targets, current baselines, and clinical expectations for risk mitigation:", body_style))
        story.append(Spacer(1, 4))
        
        sim_data = [
            [
                Paragraph("<b>Parameter</b>", bold_body_style),
                Paragraph("<b>Clinical Target Plan Detail</b>", bold_body_style)
            ],
            [
                Paragraph("Primary Target", body_style),
                Paragraph(simulator_projections.get('target_name', 'N/A'), bold_body_style)
            ],
            [
                Paragraph("Current Value", body_style),
                Paragraph(simulator_projections.get('current_val_str', 'N/A'), body_style)
            ],
            [
                Paragraph("Target Value", body_style),
                Paragraph(simulator_projections.get('target_val_str', 'N/A'), body_style)
            ],
            [
                Paragraph("Priority", body_style),
                Paragraph(simulator_projections.get('priority_label', 'N/A'), bold_body_style)
            ],
            [
                Paragraph("Expected Outcome", body_style),
                Paragraph(simulator_projections.get('expected_outcome', 'Risk Reduction Expected'), body_style)
            ],
            [
                Paragraph("Estimated Timeline", body_style),
                Paragraph(simulator_projections.get('estimated_timeline', '3–6 Months'), body_style)
            ]
        ]
        
        sim_table = Table(sim_data, colWidths=[180, doc.width - 180])
        sim_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ECFDF5")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(sim_table)
        story.append(Spacer(1, 10))
        
    # Page Break for Recommendations
    story.append(PageBreak())
    
    # Header for Page 2
    story.append(Paragraph("CLINICAL RISK ASSESSMENT REPORT", title_style))
    story.append(Paragraph("AI-Powered Health Risk Predictor • Actionable Care Plans", subtitle_style))
    story.append(Spacer(1, 5))
    
    # 4. Personalized Recommendations
    story.append(Paragraph("4. Personalized Preventive Recommendations", section_heading))
    story.append(Paragraph("Based on clinical screening parameters, the following action plans have been generated (maximum 4 points per category):", body_style))
    story.append(Spacer(1, 6))
    
    def clean_rec_text(text):
        t = re.sub(r'[*`#_]', '', text)
        t = t.replace("\n", "<br/>")
        return t
        
    rec_data = [
        [
            Paragraph("<b>🥗 Dietary Plan</b>", bold_body_style),
            Paragraph(clean_rec_text(recommendations.get('diet', 'No recommendations.')), body_style)
        ],
        [
            Paragraph("<b>🏃 Exercise Regimen</b>", bold_body_style),
            Paragraph(clean_rec_text(recommendations.get('exercise', 'No recommendations.')), body_style)
        ],
        [
            Paragraph("<b>😴 Lifestyle & Sleep</b>", bold_body_style),
            Paragraph(clean_rec_text(recommendations.get('lifestyle', 'No recommendations.')), body_style)
        ],
        [
            Paragraph("<b>🩺 Preventive Monitoring</b>", bold_body_style),
            Paragraph(clean_rec_text(recommendations.get('preventive', 'No recommendations.')), body_style)
        ]
    ]
    
    rec_table = Table(rec_data, colWidths=[140, doc.width - 140])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), BACKGROUND_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(rec_table)
    story.append(Spacer(1, 15))
    
    # Disclaimer block (Required for clinical apps)
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=1, # Centered
        leading=10
    )
    
    disclaimer_text = (
        "<b>MEDICAL DISCLAIMER:</b> This report is generated by an Artificial Intelligence screening tool "
        "and is intended solely for educational and portfolio demonstration purposes. It does NOT constitute "
        "medical advice, formal diagnosis, or treatment. Please present this report to a qualified "
        "healthcare practitioner or physician to receive standard clinical diagnosis and management."
    )
    
    story.append(KeepTogether([
        Spacer(1, 10),
        Paragraph(disclaimer_text, disclaimer_style)
    ]))
    
    # Page Number Canvas callback
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor("#7F8C8D"))
        
        # Draw line separator above footer
        canvas.setStrokeColor(BORDER_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(40, 25, doc.pagesize[0]-40, 25)
        
        # Footer text
        page_num = canvas.getPageNumber()
        canvas.drawString(40, 15, "Health Risk Predictor App — Portfolio Demonstration")
        canvas.drawRightString(doc.pagesize[0]-40, 15, f"Page {page_num} of 2")
        canvas.restoreState()
        
    # Build PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF Report generated successfully at: {output_path}")
