import os
from dotenv import load_dotenv
load_dotenv()

import re
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Imports from custom helpers
from ml_model import load_model, predict_patient_risk, explain_local_risk, calculate_bmi
from report_generator import generate_pdf_report
from ai_helper import generate_ai_recommendations, get_ai_chat_response, DEFAULT_MODEL
from ocr_helper import parse_metrics_from_text, extract_text_from_pdf, extract_text_from_image, MOCK_REPORTS, parse_clinical_report_with_confidence, clean_extracted_text

# Initialize FastAPI App
app = FastAPI(
    title="Health Risk Predictor API",
    description="Backend API for Cardiometabolic Risk intelligence, OCR extraction, AI Chat, and PDF Exports.",
    version="2.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model
model_data = load_model('model.joblib')
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Data Models
class PatientMetrics(BaseModel):
    name: Optional[str] = "Anonymous"
    age: int
    gender: str
    height: float
    weight: float
    systolic_bp: int
    diastolic_bp: int
    glucose: float
    cholesterol: float
    smoking_status: str
    alcohol_consumption: str
    physical_activity: str
    family_history: str

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    patient_context: Dict[str, Any]

class ExportRequest(BaseModel):
    patient_dict: Dict[str, Any]
    risk_score: float
    risk_category: str
    risk_drivers: List[Dict[str, Any]]
    recommendations: Dict[str, str]
    simulator_projections: Dict[str, Any]
    priority_areas: List[str]
    exec_summary: str

@app.post("/api/analyze")
def analyze_risk(metrics: PatientMetrics):
    try:
        patient_dict = {
            'age': metrics.age,
            'gender': metrics.gender if metrics.gender != "Select" else "Female",
            'height': metrics.height,
            'weight': metrics.weight,
            'bmi': calculate_bmi(metrics.weight, metrics.height),
            'systolic_bp': metrics.systolic_bp,
            'diastolic_bp': metrics.diastolic_bp,
            'glucose': metrics.glucose,
            'cholesterol': metrics.cholesterol,
            'smoking_status': metrics.smoking_status if metrics.smoking_status != "Select" else "Non-Smoker",
            'alcohol_consumption': metrics.alcohol_consumption if metrics.alcohol_consumption != "Select" else "None",
            'physical_activity': metrics.physical_activity if metrics.physical_activity != "Select" else "Moderate",
            'family_history': metrics.family_history if metrics.family_history != "Select" else "No"
        }

        # Run Predictions
        cat, score, conf = predict_patient_risk(patient_dict, model_data)
        drivers = explain_local_risk(patient_dict, model_data)

        # Get top driver feature and label
        if drivers:
            top_driver_name = drivers[0]['label']
            feat = drivers[0]['feature']
        else:
            top_driver_name = "None"
            feat = "general"

        # Determine Plan & Colors
        if cat == "High Risk":
            rec_plan = "Urgent Consultation"
        elif cat == "Moderate Risk":
            rec_plan = "Lifestyle Intervention"
        else:
            rec_plan = "Routine Monitoring"

        # Executive Clinical Summary Sentence
        if cat == "Low Risk":
            exec_summary = "Patient demonstrates low cardiometabolic risk. Routine monitoring and healthy lifestyle maintenance are recommended."
        else:
            exec_summary = f"Patient demonstrates {cat.lower()} cardiometabolic risk primarily driven by {top_driver_name.lower()}. {rec_plan} and clinical follow-up are recommended."

        # Recommended Actions (Exactly 4 checkmark actions based on top driver)
        if 'glucose' in feat or 'sugar' in feat:
            actions = [
                "Reduce refined carbohydrates",
                "Walk after meals",
                "Monitor fasting glucose",
                "Schedule HbA1c testing"
            ]
        elif 'bp' in feat or 'systolic' in feat or 'diastolic' in feat or 'pressure' in feat:
            actions = [
                "Reduce sodium intake",
                "Maintain daily activity",
                "Monitor blood pressure",
                "Follow physician recommendations"
            ]
        elif 'bmi' in feat or 'weight' in feat:
            actions = [
                "Establish safe caloric deficit",
                "Combine walking & strength training",
                "Prioritize 7-8 hours of quality sleep",
                "Monitor weight weekly under consistent conditions"
            ]
        elif 'cholesterol' in feat or 'lipid' in feat or 'chol' in feat:
            actions = [
                "Swap saturated fats for healthy plant oils",
                "Increase soluble fiber intake (oats, legumes)",
                "Walk/exercise 150 minutes weekly",
                "Recheck complete lipid panel in 3 months"
            ]
        else:
            actions = [
                "Adopt Mediterranean-style nutrition",
                "Walk 30 minutes daily",
                "Annual clinical risk screenings",
                "Maintain regular sleep and hydration"
            ]

        # Clinical Interpretation Bullets (Up to 4 concise dynamic interpretations)
        interpretation_bullets = []
        # Bullet 1: Primary driver
        if 'glucose' in feat or 'sugar' in feat:
            interpretation_bullets.append("Elevated blood glucose is the strongest contributor to the patient's cardiometabolic risk profile.")
        elif 'bmi' in feat or 'weight' in feat:
            interpretation_bullets.append("Body weight and BMI indicate increased metabolic burden and represent the primary risk driver.")
        elif 'bp' in feat or 'systolic' in feat or 'diastolic' in feat or 'pressure' in feat:
            interpretation_bullets.append("Elevated blood pressure is the primary contributor to increased cardiovascular and metabolic risk.")
        elif 'cholesterol' in feat or 'lipid' in feat or 'chol' in feat:
            interpretation_bullets.append("Elevated lipid and cholesterol levels serve as the principal driver of the patient's metabolic risk.")
        else:
            interpretation_bullets.append("Overall biomarker evaluation serves as the primary basis for the clinical risk assessment.")

        # Collect secondary factors
        secondary_candidates = []
        if not ('glucose' in feat or 'sugar' in feat) and patient_dict['glucose'] >= 100.0:
            secondary_candidates.append("Fasting blood glucose is elevated and contributes to insulin sensitivity concerns.")
        if not ('bmi' in feat or 'weight' in feat) and patient_dict['bmi'] >= 25.0:
            secondary_candidates.append("Body weight and BMI indicate increased metabolic burden and should be monitored closely.")
        if not ('bp' in feat or 'systolic' in feat or 'diastolic' in feat or 'pressure' in feat) and (patient_dict['systolic_bp'] >= 130 or patient_dict['diastolic_bp'] >= 80):
            secondary_candidates.append("Blood pressure remains a secondary risk factor that may benefit from lifestyle optimization.")
        if not ('cholesterol' in feat or 'lipid' in feat or 'chol' in feat) and patient_dict['cholesterol'] >= 200.0:
            secondary_candidates.append("Cholesterol and lipid metrics show mild elevation and warrant dietary modifications.")

        # Backup candidates
        if len(secondary_candidates) < 2:
            if patient_dict['physical_activity'] == 'Low':
                secondary_candidates.append("Sedentary lifestyle habits contribute to slower metabolic clearance and higher risk.")
            else:
                secondary_candidates.append("Age and systemic metabolic factors play a secondary role in overall cardiovascular risk.")
        if len(secondary_candidates) < 2:
            if patient_dict['smoking_status'] == 'Smoker':
                secondary_candidates.append("Active tobacco use acts as an independent accelerator for cardiovascular risks.")
            else:
                secondary_candidates.append("Maintaining consistent daily physical activity supports cardiovascular resilience.")

        interpretation_bullets.append(secondary_candidates[0])
        if len(secondary_candidates) > 1:
            interpretation_bullets.append(secondary_candidates[1])

        # Bullet 4: Risk category
        if cat == "High Risk":
            interpretation_bullets.append("Urgent clinical consultation and targeted pharmacological evaluation are recommended to mitigate risk.")
        elif cat == "Moderate Risk":
            interpretation_bullets.append("Lifestyle intervention and periodic clinical follow-up are expected to reduce future risk.")
        else:
            interpretation_bullets.append("Continuous adherence to healthy nutrition and regular exercise will sustain low risk levels.")

        # Priority Intervention Plan Target Selection
        target_name = "Maintain Healthy Lifestyle"
        curr_val_str = "--"
        tgt_val_str = "Healthy baselines"
        priority_label = "Low"
        expected_outcome = "Maintain low risk levels"

        if cat != "Low Risk" and drivers:
            # Pick highest driver that is out of range
            for d in drivers:
                f_name = d['feature']
                if f_name == 'glucose' and patient_dict['glucose'] >= 100.0:
                    target_name = "Fasting Blood Glucose"
                    curr_val_str = f"{patient_dict['glucose']:.0f} mg/dL"
                    tgt_val_str = "< 100 mg/dL"
                    priority_label = "High" if d['contribution'] >= 15.0 else "Medium"
                    expected_outcome = "Glycemic Control & Insulin Sensitivity Reset"
                    break
                elif f_name in ['systolic_bp', 'diastolic_bp'] and (patient_dict['systolic_bp'] >= 120 or patient_dict['diastolic_bp'] >= 80):
                    target_name = "Systolic / Diastolic Blood Pressure"
                    curr_val_str = f"{patient_dict['systolic_bp']:.0f}/{patient_dict['diastolic_bp']:.0f} mmHg"
                    tgt_val_str = "< 120/80 mmHg"
                    priority_label = "High" if d['contribution'] >= 15.0 else "Medium"
                    expected_outcome = "Cardiovascular Strain Mitigation"
                    break
                elif f_name == 'bmi' and (patient_dict['bmi'] >= 25.0 or patient_dict['bmi'] < 18.5):
                    target_name = "Body Mass Index (Weight Status)"
                    curr_val_str = f"{patient_dict['bmi']:.1f} (Weight: {patient_dict['weight']:.1f} kg)"
                    tgt_val_str = "18.5 – 24.9"
                    priority_label = "High" if d['contribution'] >= 15.0 else "Medium"
                    expected_outcome = "Somatic Weight Reduction & Lipotoxicity Reversal"
                    break
                elif f_name == 'cholesterol' and patient_dict['cholesterol'] >= 200.0:
                    target_name = "Total Blood Cholesterol"
                    curr_val_str = f"{patient_dict['cholesterol']:.0f} mg/dL"
                    tgt_val_str = "< 200 mg/dL"
                    priority_label = "High" if d['contribution'] >= 15.0 else "Medium"
                    expected_outcome = "Atherosclerotic Plaque Stabilization"
                    break

        sim_proj = {
            'target_name': target_name,
            'current_val_str': curr_val_str,
            'target_val_str': tgt_val_str,
            'priority_label': priority_label,
            'expected_outcome': expected_outcome,
            'estimated_timeline': "3–6 Months"
        }

        # Nutrition / Activity / Monitoring Cards
        # Nutrition plan
        if 'glucose' in feat or patient_dict['glucose'] >= 100.0:
            nut_bullets = [
                "Focus on low-glycemic foods (vegetables, legumes, whole grains)",
                "Avoid simple starches, white rice, and sugary sodas",
                "Ensure lean protein and healthy fats are present at each meal"
            ]
        elif 'cholesterol' in feat or patient_dict['cholesterol'] >= 200.0:
            nut_bullets = [
                "Increase soluble fiber intake (oats, barley, lentils)",
                "Avoid saturated fats, fatty red meats, and full-fat butter",
                "Swap tropical oils for olive oil and eat raw walnuts"
            ]
        elif 'bp' in feat or patient_dict['systolic_bp'] >= 130:
            nut_bullets = [
                "Strictly limit sodium intake below 1500mg daily (DASH diet)",
                "Prioritize potassium-rich sweet potatoes, spinach, and bananas",
                "Avoid cured meats, processed soups, and high-sodium seasonings"
            ]
        else:
            nut_bullets = [
                "Maintain a balanced, calorie-neutral Mediterranean diet",
                "Incorporate fresh leafy greens and antioxidant-rich berries",
                "Stay consistently hydrated with at least 2 liters of water daily"
            ]

        # Activity plan
        if 'bmi' in feat or patient_dict['bmi'] >= 25.0:
            act_bullets = [
                "Engage in 150 minutes of moderate aerobic cardio weekly",
                "Incorporate 2 sessions of strength training to build lean mass",
                "Maintain a daily target of 8,000–10,000 active steps"
            ]
        else:
            act_bullets = [
                "Commit to a brisk 30-minute daily walk after meals",
                "Combine light cardiorespiratory exercises with mobility stretching",
                "Avoid sedentary blocks by standing 5 minutes every hour"
            ]

        # Monitoring plan
        mon_bullets = []
        if 'glucose' in feat or patient_dict['glucose'] >= 100.0:
            mon_bullets.append("Measure fasting blood glucose weekly at home")
        else:
            mon_bullets.append("Verify blood glucose level annually at routine labs")

        if 'bp' in feat or patient_dict['systolic_bp'] >= 130:
            mon_bullets.append("Monitor blood pressure daily under resting conditions")
        else:
            mon_bullets.append("Assess resting blood pressure once per week")

        if 'cholesterol' in feat or patient_dict['cholesterol'] >= 200.0:
            mon_bullets.append("Order a complete lipid panel panel in 3 months")
        else:
            mon_bullets.append("Routine lipid panel screening once every year")

        # Generate Recommendations via AI/Mock
        recommendations, _ = generate_ai_recommendations(
            patient_dict=patient_dict,
            risk_score=score,
            risk_category=cat,
            risk_drivers=drivers,
            api_key=GROQ_API_KEY
        )

        return {
            "success": True,
            "patient_dict": patient_dict,
            "risk_score": score,
            "risk_category": cat,
            "confidence_score": conf,
            "risk_drivers": drivers,
            "exec_summary": exec_summary,
            "recommended_actions": actions,
            "clinical_interpretation": interpretation_bullets,
            "simulator_projections": sim_proj,
            "nutrition_bullets": nut_bullets,
            "activity_bullets": act_bullets,
            "monitoring_bullets": mon_bullets,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_assistant(request: ChatRequest):
    try:
        response = get_ai_chat_response(
            messages=request.messages,
            patient_context=request.patient_context,
            api_key=GROQ_API_KEY
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_medical_report(file: UploadFile = File(...)):
    filename = file.filename
    
    # Save to temp file
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        ext = os.path.splitext(filename)[1].lower()
        extracted_text = ""
        avg_confidence = 100.0 # Default to 100% for digital PDF
        
        if ext == ".pdf":
            extracted_text = extract_text_from_pdf(temp_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            extracted_text, avg_confidence, ocr_success = extract_text_from_image(temp_path)
            if not ocr_success:
                return {
                    "success": False,
                    "filename": filename,
                    "status": "OCR Engine Unavailable",
                    "error": "Tesseract OCR engine is not installed or configured on the system path.",
                    "parameters": [],
                    "text": "",
                    "ocr_confidence": 0.0
                }
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")

        cleaned_text = clean_extracted_text(extracted_text)
        if not cleaned_text.strip():
            return {
                "success": False,
                "filename": filename,
                "status": "No text extracted",
                "error": "The uploaded document appears to be empty or unreadable.",
                "parameters": [],
                "text": "",
                "ocr_confidence": avg_confidence
            }

        # Parse parameters with confidence scores
        parameters = parse_clinical_report_with_confidence(cleaned_text)
        
        if not parameters:
            return {
                "success": False,
                "filename": filename,
                "status": "No parameters found",
                "error": "No valid clinical parameters could be extracted from this report.",
                "parameters": [],
                "text": cleaned_text,
                "ocr_confidence": avg_confidence
            }

        return {
            "success": True,
            "filename": filename,
            "status": "Extraction Successful",
            "metrics_count": len(parameters),
            "parameters": parameters,
            "text": cleaned_text,
            "ocr_confidence": avg_confidence
        }
    except Exception as e:
        return {
            "success": False,
            "filename": filename,
            "status": "Extraction Failed",
            "error": f"Error parsing report: {str(e)}",
            "parameters": [],
            "text": "",
            "ocr_confidence": 0.0
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/mock_scenario/{scenario_name}")
def get_mock_scenario(scenario_name: str):
    if scenario_name in MOCK_REPORTS:
        mock_data = MOCK_REPORTS[scenario_name]
        extracted_values = mock_data["extracted_values"]
        parameters = []
        
        field_mappings = {
            "name": ("Full Name", "patient-name", "98%"),
            "age": ("Age", "patient-age", "95%"),
            "gender": ("Gender", "patient-gender", "97%"),
            "height": ("Height (cm)", "patient-height", "93%"),
            "weight": ("Weight (kg)", "patient-weight", "94%"),
            "systolic_bp": ("Systolic BP", "patient-sys-bp", "96%"),
            "diastolic_bp": ("Diastolic BP", "patient-dia-bp", "96%"),
            "glucose": ("Blood Glucose", "patient-glucose", "96%"),
            "cholesterol": ("Total Cholesterol", "patient-cholesterol", "96%"),
            "smoking_status": ("Smoking Status", "patient-smoking", "90%"),
            "alcohol_consumption": ("Alcohol Consumption", "patient-alcohol", "92%"),
            "physical_activity": ("Physical Activity Level", "patient-activity", "91%"),
            "family_history": ("Family History", "patient-family-hist", "93%")
        }
        
        for key, val in extracted_values.items():
            if key in field_mappings:
                name, field, conf = field_mappings[key]
                parameters.append({
                    "name": name,
                    "value": val,
                    "confidence": conf,
                    "field": field
                })
                
        # Inject standard mock pathology report markers (Vitamin B12, D, Creatinine) to match user expectations
        if "high_risk" in scenario_name:
            parameters.append({"name": "Vitamin B12", "value": "132.5", "confidence": "92%", "field": None})
            parameters.append({"name": "Vitamin D", "value": "12.4", "confidence": "94%", "field": None})
            parameters.append({"name": "Creatinine", "value": "1.34", "confidence": "97%", "field": None})
        elif "moderate_risk" in scenario_name:
            parameters.append({"name": "Vitamin B12", "value": "189.2", "confidence": "92%", "field": None})
            parameters.append({"name": "Vitamin D", "value": "24.1", "confidence": "94%", "field": None})
            parameters.append({"name": "Creatinine", "value": "0.95", "confidence": "97%", "field": None})
        else:
            parameters.append({"name": "Vitamin B12", "value": "450.0", "confidence": "92%", "field": None})
            parameters.append({"name": "Vitamin D", "value": "35.5", "confidence": "94%", "field": None})
            parameters.append({"name": "Creatinine", "value": "0.82", "confidence": "97%", "field": None})
            
        return {
            "success": True,
            "filename": scenario_name,
            "status": "Extraction Successful (Simulated Scenario)",
            "metrics_count": len(parameters),
            "parameters": parameters,
            "text": mock_data["text"]
        }
    else:
        raise HTTPException(status_code=404, detail="Mock scenario not found")

@app.post("/api/export")
def export_pdf(request: ExportRequest):
    pdf_filename = f"health_report_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join("static", pdf_filename)
    os.makedirs("static", exist_ok=True)
    
    try:
        generate_pdf_report(
            patient_dict=request.patient_dict,
            risk_score=request.risk_score,
            risk_category=request.risk_category,
            risk_drivers=request.risk_drivers,
            recommendations=request.recommendations,
            simulator_projections=request.simulator_projections,
            priority_areas=request.priority_areas,
            output_path=pdf_path,
            exec_summary=request.exec_summary
        )
        return {"pdf_url": f"/{pdf_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Static Files
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Start server
    uvicorn.run("app:app", host="0.0.0.0", port=8501, reload=True)
