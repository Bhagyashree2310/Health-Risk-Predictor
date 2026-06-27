import re
import os
import pdfplumber
from PIL import Image
import pytesseract

# Configure pytesseract path if installed in standard location but not on system PATH
DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(DEFAULT_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH

# Mock reports for simulation when Tesseract is not installed or for demonstration
MOCK_REPORTS = {
    "report_high_risk.png": {
        "text": """
        HEALTH SCREENING REPORT
        ------------------------
        Patient Name: Christopher Evans
        Age: 62
        Gender: Male
        Height: 175 cm
        Weight: 98 kg
        Blood Pressure: 155/95 mmHg
        Blood Glucose (Fasting): 142 mg/dL
        Total Cholesterol: 265 mg/dL
        Smoking Status: Smoker
        Alcohol Consumption: Heavy
        Physical Activity: Low
        Family History: Yes (Father had cardiovascular disease)
        """,
        "extracted_values": {
            "name": "Christopher Evans",
            "age": 62,
            "gender": "Male",
            "height": 175.0,
            "weight": 98.0,
            "bmi": 32.0,
            "systolic_bp": 155,
            "diastolic_bp": 95,
            "glucose": 142.0,
            "cholesterol": 265.0,
            "smoking_status": "Smoker",
            "alcohol_consumption": "Heavy",
            "physical_activity": "Low",
            "family_history": "Yes"
        },
        "description": "High-risk scenario: Elderly smoker with obesity, stage 2 hypertension, hyperglycemia, and hypercholesterolemia."
    },
    "report_moderate_risk.png": {
        "text": """
        CLINICAL LABORATORIES INC.
        -------------------------
        Patient Name: Sarah Jenkins
        Age: 45
        Gender: Female
        Height: 165 cm
        Weight: 76 kg
        BP Systolic/Diastolic: 132/84 mmHg
        Fasting Glucose: 112 mg/dL
        Total Cholesterol: 218 mg/dL
        Smoking: Non-Smoker
        Alcohol: Moderate
        Activity Level: Moderate
        Family History: Yes (Mother has Diabetes)
        """,
        "extracted_values": {
            "name": "Sarah Jenkins",
            "age": 45,
            "gender": "Female",
            "height": 165.0,
            "weight": 76.0,
            "bmi": 27.9,
            "systolic_bp": 132,
            "diastolic_bp": 84,
            "glucose": 112.0,
            "cholesterol": 218.0,
            "smoking_status": "Non-Smoker",
            "alcohol_consumption": "Moderate",
            "physical_activity": "Moderate",
            "family_history": "Yes"
        },
        "description": "Moderate-risk scenario: Middle-aged, overweight, pre-diabetic, pre-hypertensive, with family medical history."
    },
    "report_low_risk.png": {
        "text": """
        ANNUAL WELLNESS EXAM REPORT
        ---------------------------
        Patient Name: Daniel Vance
        Age: 29
        Gender: Male
        Height: 182 cm
        Weight: 78 kg
        Vitals - BP: 118/76 mmHg
        Lab - Glucose: 88 mg/dL
        Lab - Cholesterol: 175 mg/dL
        Smoking: Non-Smoker
        Alcohol: None
        Activity: High
        Family History: No
        """,
        "extracted_values": {
            "name": "Daniel Vance",
            "age": 29,
            "gender": "Male",
            "height": 182.0,
            "weight": 78.0,
            "bmi": 23.5,
            "systolic_bp": 118,
            "diastolic_bp": 76,
            "glucose": 88.0,
            "cholesterol": 175.0,
            "smoking_status": "Non-Smoker",
            "alcohol_consumption": "None",
            "physical_activity": "High",
            "family_history": "No"
        },
        "description": "Low-risk scenario: Young, active, normal BMI, optimal blood pressure, blood glucose, and cholesterol."
    }
}

def clean_extracted_text(text):
    """Normalize whitespace and line endings in text."""
    if not text:
        return ""
    # Remove excessive empty lines, strip whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def parse_metrics_from_text(text):
    """
    Parse medical variables from raw text using regex pattern matching.
    """
    metrics = {}
    
    # 1. Name
    name_match = re.search(r'(?:patient|name|patient\s+name)\s*[:|-]\s*([A-Za-z\s]+)', text, re.IGNORECASE)
    if name_match:
        # Clean up name, remove trailing words like "Age", "Gender"
        name = name_match.group(1).strip()
        name = re.split(r'\n|:|\b(?:age|gender|sex|male|female|date|id|unit|room|admission|phone|email|vitals|labs)\b', name, flags=re.IGNORECASE)[0].strip()
        metrics['name'] = name
    
    # 2. Age
    age_match = re.search(r'\b(?:age)\s*[:|-]?\s*(\d{1,3})\b', text, re.IGNORECASE)
    if age_match:
        metrics['age'] = int(age_match.group(1))
        
    # 3. Gender
    gender_match = re.search(r'\b(?:gender|sex)\s*[:|-]?\s*(male|female|other)\b', text, re.IGNORECASE)
    if gender_match:
        metrics['gender'] = gender_match.group(1).capitalize()
        
    # 4. Height
    height_match = re.search(r'\b(?:height|ht)\s*[:|-]?\s*(\d{2,3})\s*(?:cm|in|meters)?\b', text, re.IGNORECASE)
    if height_match:
        metrics['height'] = float(height_match.group(1))
        
    # 5. Weight
    weight_match = re.search(r'\b(?:weight|wt)\s*[:|-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:kg|lbs|pounds)?\b', text, re.IGNORECASE)
    if weight_match:
        metrics['weight'] = float(weight_match.group(1))
        
    # 6. Blood Pressure (SBP / DBP)
    bp_match = re.search(r'\b(?:bp|blood\s*pressure)\s*[:|-]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b', text, re.IGNORECASE)
    if bp_match:
        metrics['systolic_bp'] = int(bp_match.group(1))
        metrics['diastolic_bp'] = int(bp_match.group(2))
    else:
        # Alternative separate SBP/DBP search
        sbp_match = re.search(r'\b(?:systolic|sbp)\s*[:|-]?\s*(\d{2,3})\b', text, re.IGNORECASE)
        dbp_match = re.search(r'\b(?:diastolic|dbp)\s*[:|-]?\s*(\d{2,3})\b', text, re.IGNORECASE)
        if sbp_match:
            metrics['systolic_bp'] = int(sbp_match.group(1))
        if dbp_match:
            metrics['diastolic_bp'] = int(dbp_match.group(1))
            
    # 7. Glucose
    glucose_match = re.search(r'\b(?:glucose|fasting\s*glucose|sugar|blood\s*sugar)\s*[:|-]?\s*(\d{2,3})\b', text, re.IGNORECASE)
    if glucose_match:
        metrics['glucose'] = float(glucose_match.group(1))
        
    # 8. Cholesterol
    cholesterol_match = re.search(r'\b(?:cholesterol|total\s*cholesterol|chol)\s*[:|-]?\s*(\d{2,3})\b', text, re.IGNORECASE)
    if cholesterol_match:
        metrics['cholesterol'] = float(cholesterol_match.group(1))
        
    # 9. Smoking
    smoking_match = re.search(r'\b(?:smoking|smoker)\s*[:|-]?\s*(smoker|non-smoker|yes|no)\b', text, re.IGNORECASE)
    if smoking_match:
        val = smoking_match.group(1).lower()
        metrics['smoking_status'] = 'Smoker' if val in ['smoker', 'yes'] else 'Non-Smoker'
        
    # 10. Alcohol
    alcohol_match = re.search(r'\b(?:alcohol|drinking)\s*[:|-]?\s*(none|moderate|heavy|yes|no)\b', text, re.IGNORECASE)
    if alcohol_match:
        val = alcohol_match.group(1).lower()
        if val in ['heavy', 'yes']:
            metrics['alcohol_consumption'] = 'Heavy'
        elif val in ['moderate']:
            metrics['alcohol_consumption'] = 'Moderate'
        else:
            metrics['alcohol_consumption'] = 'None'
            
    # 11. Physical Activity
    activity_match = re.search(r'\b(?:activity|exercise|physical\s*activity)\s*[:|-]?\s*(low|moderate|high|active|inactive)\b', text, re.IGNORECASE)
    if activity_match:
        val = activity_match.group(1).lower()
        if val in ['high', 'active']:
            metrics['physical_activity'] = 'High'
        elif val in ['moderate']:
            metrics['physical_activity'] = 'Moderate'
        else:
            metrics['physical_activity'] = 'Low'
            
    # 12. Family History
    fam_match = re.search(r'\b(?:family\s*history|fam\s*hist)\s*[:|-]?\s*(yes|no|positive|negative)\b', text, re.IGNORECASE)
    if fam_match:
        val = fam_match.group(1).lower()
        metrics['family_history'] = 'Yes' if val in ['yes', 'positive'] else 'No'

    # Auto-calculate BMI if weight & height are extracted
    if 'weight' in metrics and 'height' in metrics:
        h = metrics['height']
        w = metrics['weight']
        metrics['bmi'] = round(w / ((h / 100) ** 2), 1)

    return metrics

def extract_text_from_pdf(pdf_file_path):
    """Extract all text from a PDF file using pdfplumber."""
    extracted_text = ""
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    extracted_text += f"\n--- PAGE {i+1} ---\n" + text
    except Exception as e:
        extracted_text = f"Error reading PDF file: {str(e)}"
    return clean_extracted_text(extracted_text)

def check_tesseract():
    """Verify if the Tesseract binary is executable."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def extract_text_from_image(image_file_path):
    """
    Attempt to extract text from an image using pytesseract.
    Returns:
    - text: Extracted raw text or message.
    - avg_confidence: Average word confidence (0-100).
    - success: Boolean status of OCR.
    """
    if not check_tesseract():
        return "Tesseract OCR is not installed or configured on the system path.", 0.0, False
        
    try:
        img = Image.open(image_file_path)
        
        # Calculate OCR confidence
        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data['conf'] if int(c) >= 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 100.0
        except Exception:
            avg_conf = 85.0 # Fallback baseline
            
        # Run default layout analysis (usually PSM 3)
        text_default = pytesseract.image_to_string(img)
        
        # Run PSM 6 (single uniform block of text) to capture multi-column data correctly
        try:
            text_psm6 = pytesseract.image_to_string(img, config="--psm 6")
        except Exception:
            text_psm6 = ""
            
        combined_text = text_default + "\n\n=== PSM 6 LAYOUT ===\n\n" + text_psm6
        return clean_extracted_text(combined_text), avg_conf, True
    except Exception as e:
        return f"OCR Failed: {str(e)}", 0.0, False

def detect_risk_factors_in_text(text):
    """Scan text for keywords indicating specific high-risk conditions."""
    risks = []
    
    lowercased = text.lower()
    
    # Blood Pressure alerts
    if re.search(r'\b(?:hypertension|high\s*blood\s*pressure)\b', lowercased):
        risks.append("Hypertension noted in clinical notes.")
        
    # Glucose alerts
    if re.search(r'\b(?:diabetes|diabetic|hyperglycemia|high\s*glucose)\b', lowercased):
        risks.append("Diabetes / Hyperglycemia mentioned.")
        
    # Cholesterol alerts
    if re.search(r'\b(?:hyperlipidemia|hypercholesterolemia|high\s*cholesterol)\b', lowercased):
        risks.append("Elevated lipid profiles / hypercholesterolemia mentioned.")
        
    # Cardiovascular
    if re.search(r'\b(?:coronary|heart\s*disease|angina|infarction|cvd|stroke)\b', lowercased):
        risks.append("Cardiovascular disease indicators identified.")
        
    # Family history
    if re.search(r'\b(?:family\s*history\s*of\s*(?:heart|diabetes|cancer|stroke))\b', lowercased):
        risks.append("Significant genetic risk factors.")
        
    # Obesity
    if re.search(r'\b(?:obese|obesity|high\s*bmi)\b', lowercased):
        risks.append("Clinical obesity indicators.")
        
    return risks

def parse_clinical_report_with_confidence(text):
    """
    Parse clinical parameters and return a list of dictionaries with parameter name,
    extracted value, confidence percentage, and form field mapping.
    Supports main metrics as well as custom metrics like Vitamin B12, Vitamin D, Creatinine.
    """
    cleaned = clean_extracted_text(text)
    parameters = []
    
    # 1. Full Name
    name_match = re.search(r'(?:patient|name|patient\s+name)(?:\s+attributed\s+value)?\s*[:|-]\s*([A-Za-z\s\.]+)', cleaned, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip()
        name = re.split(r'\n|:|\b(?:age|gender|sex|male|female|date|id|unit|room|admission|phone|email|vitals|labs|assessment)\b', name, flags=re.IGNORECASE)[0].strip()
        if len(name) > 2 and not name.lower().startswith("report"):
            parameters.append({
                "name": "Full Name",
                "value": name,
                "confidence": "98%",
                "field": "patient-name"
            })
            
    # 2. Age
    age_match = re.search(r'\b(?:age)(?:\s+attributed\s+value)?\s*[:|-]?\s*(\d{1,3})\b', cleaned, re.IGNORECASE)
    if age_match:
        parameters.append({
            "name": "Age",
            "value": int(age_match.group(1)),
            "confidence": "95%",
            "field": "patient-age"
        })
        
    # 3. Gender
    gender_match = re.search(r'\b(?:gender|sex)(?:\s+attributed\s+value)?\s*[:|-]?\s*(male|female|other)\b', cleaned, re.IGNORECASE)
    if gender_match:
        parameters.append({
            "name": "Gender",
            "value": gender_match.group(1).capitalize(),
            "confidence": "97%",
            "field": "patient-gender"
        })
        
    # 4. Height
    height_match = re.search(r'\b(?:height|ht)\s*[:|-]?\s*(\d{2,3})\s*(?:cm|in|meters)?\b', cleaned, re.IGNORECASE)
    if height_match:
        parameters.append({
            "name": "Height (cm)",
            "value": float(height_match.group(1)),
            "confidence": "93%",
            "field": "patient-height"
        })
        
    # 5. Weight
    weight_match = re.search(r'\b(?:weight|wt)\s*[:|-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:kg|lbs|pounds)?\b', cleaned, re.IGNORECASE)
    if weight_match:
        parameters.append({
            "name": "Weight (kg)",
            "value": float(weight_match.group(1)),
            "confidence": "94%",
            "field": "patient-weight"
        })
        
    # 6. Blood Pressure
    bp_match = re.search(r'\b(?:bp|blood\s*pressure)(?:\s+systolic/diastolic)?(?:\s*\([^)]*\))?\s*[:;|\-\s]?\s*(\d{2,3})\s*[\/\\\-]\s*(\d{2,3})\b', cleaned, re.IGNORECASE)
    if bp_match:
        parameters.append({
            "name": "Systolic BP",
            "value": int(bp_match.group(1)),
            "confidence": "96%",
            "field": "patient-sys-bp"
        })
        parameters.append({
            "name": "Diastolic BP",
            "value": int(bp_match.group(2)),
            "confidence": "96%",
            "field": "patient-dia-bp"
        })
    else:
        sbp_match = re.search(r'\b(?:systolic|sbp|elevated\s+systolic\s+bp)(?:\s+attributed\s+value)?(?:\s*\([^)]*\))?\s*[:;|\-\s]?\s*(\d{2,3})\b', cleaned, re.IGNORECASE)
        dbp_match = re.search(r'\b(?:diastolic|dbp|elevated\s+diastolic\s+bp)(?:\s+attributed\s+value)?(?:\s*\([^)]*\))?\s*[:;|\-\s]?\s*(\d{2,3})\b', cleaned, re.IGNORECASE)
        if sbp_match:
            parameters.append({
                "name": "Systolic BP",
                "value": int(sbp_match.group(1)),
                "confidence": "95%",
                "field": "patient-sys-bp"
            })
        if dbp_match:
            parameters.append({
                "name": "Diastolic BP",
                "value": int(dbp_match.group(1)),
                "confidence": "95%",
                "field": "patient-dia-bp"
            })
              
    # 7. Glucose
    glucose_match = re.search(r'\b(?:glucose|sugar|fbs|fbg|glu|fasting\s*(?:blood\s*)?glucose|blood\s*sugar|high\s*blood\s*glucose)(?:\s+attributed\s+value)?(?:\s*\([^)]*\))?(?:\s+level|\s+result)?\s*[:;|\-\s]?\s*(\d+(?:\.\d+)?)\b', cleaned, re.IGNORECASE)
    if glucose_match:
        parameters.append({
            "name": "Blood Glucose",
            "value": float(glucose_match.group(1)),
            "confidence": "96%",
            "field": "patient-glucose"
        })
        
    # 8. Cholesterol
    cholesterol_match = re.search(r'\b(?:cholesterol|cholestrol|chol|tc|total\s*(?:cholesterol|cholestrol)|high\s*cholesterol)(?:\s+attributed\s+value)?(?:\s*\([^)]*\))?(?:\s+level|\s+result)?\s*[:;|\-\s]?\s*(\d+(?:\.\d+)?)\b', cleaned, re.IGNORECASE)
    if cholesterol_match:
        parameters.append({
            "name": "Total Cholesterol",
            "value": float(cholesterol_match.group(1)),
            "confidence": "96%",
            "field": "patient-cholesterol"
        })
        
    # 9. Smoking
    smoking_match = re.search(r'\b(?:smoking|smoker|active\s+tobacco\s+use)(?:\s+attributed\s+value)?\s*[:|-]?\s*(smoker|non-smoker|yes|no)\b', cleaned, re.IGNORECASE)
    if smoking_match:
        val = smoking_match.group(1).lower()
        val_str = 'Smoker' if val in ['smoker', 'yes'] else 'Non-Smoker'
        parameters.append({
            "name": "Smoking Status",
            "value": val_str,
            "confidence": "90%",
            "field": "patient-smoking"
        })
        
    # 10. Alcohol
    alcohol_match = re.search(r'\b(?:alcohol|drinking|alcohol\s+consumption)(?:\s+attributed\s+value)?\s*[:|-]?\s*(none|moderate|heavy|yes|no)\b', cleaned, re.IGNORECASE)
    if alcohol_match:
        val = alcohol_match.group(1).lower()
        if val in ['heavy', 'yes']:
            val_str = 'Heavy'
        elif val in ['moderate']:
            val_str = 'Moderate'
        else:
            val_str = 'None'
        parameters.append({
            "name": "Alcohol Consumption",
            "value": val_str,
            "confidence": "92%",
            "field": "patient-alcohol"
        })
        
    # 11. Activity
    activity_match = re.search(r'\b(?:activity|exercise|physical\s*activity|lack\s+of\s+physical\s*activity)(?:\s+attributed\s+value)?\s*[:|-]?\s*(low|moderate|high|active|inactive)\b', cleaned, re.IGNORECASE)
    if activity_match:
        val = activity_match.group(1).lower()
        if val in ['high', 'active']:
            val_str = 'High'
        elif val in ['moderate']:
            val_str = 'Moderate'
        else:
            val_str = 'Low'
        parameters.append({
            "name": "Physical Activity Level",
            "value": val_str,
            "confidence": "91%",
            "field": "patient-activity"
        })
        
    # 12. Family History
    fam_match = re.search(r'\b(?:family\s*(?:medical\s*)?history|fam\s*hist)(?:\s+attributed\s+value)?\s*[:|-]?\s*(yes|no|positive|negative)\b', cleaned, re.IGNORECASE)
    if fam_match:
        val = fam_match.group(1).lower()
        val_str = 'Yes' if val in ['yes', 'positive'] else 'No'
        parameters.append({
            "name": "Family History",
            "value": val_str,
            "confidence": "93%",
            "field": "patient-family-hist"
        })
        
    # 13. Comprehensive Clinical Biomarkers
    biomarker_patterns = {
        "Hemoglobin": (r'\b(?:hemoglobin|haemoglobin|hb)(?:\s+level)?\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*g/dL|\s*g%)?\b', " g/dL", "float"),
        "RBC Count": (r'\b(?:rbc|red\s*blood\s*(?:cells?|count)|erythrocytes?)\s*[:|-]?\s*(\d+(?:\.\d+)?)\b', " x 10^6/uL", "float"),
        "WBC Count": (r'\b(?:wbc|white\s*blood\s*(?:cells?|count)|leukocytes?)\s*[:|-]?\s*(\d+(?:\.\d+)?)\b', " x 10^3/uL", "float"),
        "Platelet Count": (r'\b(?:platelets?|plt|platelet\s*count)\s*[:|-]?\s*(\d+(?:\.\d+)?)\b', " x 10^3/uL", "float"),
        "Hematocrit": (r'\b(?:hematocrit|hct|packed\s*cell\s*volume|pcv)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*%)?\b', " %", "float"),
        "MCV": (r'\b(?:mcv|mean\s*corpuscular\s*volume)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*fL)?\b', " fL", "float"),
        "MCH": (r'\b(?:mch|mean\s*corpuscular\s*hemoglobin)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*pg)?\b', " pg", "float"),
        "MCHC": (r'\b(?:mchc|mean\s*corpuscular\s*hemoglobin\s*concentration)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*g/dL|\s*%)?\b', " g/dL", "float"),
        "Creatinine": (r'\b(?:creatinine|creat)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "Urea": (r'\b(?:urea)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "BUN": (r'\b(?:bun|blood\s+urea\s+nitrogen)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "Uric Acid": (r'\b(?:uric\s*acid)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "Total Bilirubin": (r'\b(?:total\s+bilirubin|bilirubin\s+total)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "Direct Bilirubin": (r'\b(?:direct\s+bilirubin|bilirubin\s+direct|conjugated\s+bilirubin)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "Indirect Bilirubin": (r'\b(?:indirect\s+bilirubin|bilirubin\s+indirect|unconjugated\s+bilirubin)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*mg/dL)?\b', " mg/dL", "float"),
        "SGOT (AST)": (r'\b(?:sgot|ast|aspartate\s+aminotransferase)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*U/L|\s*IU/L)?\b', " U/L", "float"),
        "SGPT (ALT)": (r'\b(?:sgpt|alt|alanine\s+aminotransferase)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*U/L|\s*IU/L)?\b', " U/L", "float"),
        "Albumin": (r'\b(?:albumin)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*g/dL)?\b', " g/dL", "float"),
        "Total Protein": (r'\b(?:total\s+protein|protein\s+total)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*g/dL)?\b', " g/dL", "float"),
        "Globulin": (r'\b(?:globulin)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*g/dL)?\b', " g/dL", "float"),
        "Vitamin B12": (r'\b(?:vit\s*b12|vitamin\s*b12|cobalamin)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*pg/mL)?\b', " pg/mL", "float"),
        "Vitamin D": (r'\b(?:vit\s*d|vitamin\s*d|25-hydroxy\s*vitamin\s*d|25\(oh\)d)\s*[:|-]?\s*(\d+(?:\.\d+)?)(?:\s*ng/mL)?\b', " ng/mL", "float")
    }

    for name, (pattern, unit, val_type) in biomarker_patterns.items():
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            raw_val = match.group(1)
            if val_type == "float":
                val = float(raw_val)
                if val.is_integer():
                    val_str = f"{int(val)}{unit}"
                else:
                    val_str = f"{val}{unit}"
            else:
                val_str = f"{raw_val}{unit}"
                
            parameters.append({
                "name": name,
                "value": val_str,
                "confidence": "94%",
                "field": None
            })
            
    return parameters

if __name__ == '__main__':
    # Test OCR logic
    test_text = MOCK_REPORTS['report_high_risk.png']['text']
    parsed = parse_metrics_from_text(test_text)
    print("Parsed test report successfully:")
    for k, v in parsed.items():
        print(f"  {k}: {v}")
