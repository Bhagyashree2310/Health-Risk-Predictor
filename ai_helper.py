import os
import re
from dotenv import load_dotenv
load_dotenv()

from groq import Groq

# Default model
DEFAULT_MODEL = "llama-3.3-70b-versatile"

def get_groq_client(api_key=None):
    """
    Return a Groq client. Uses provided API key first,
    falls back to GROQ_API_KEY env variable, or returns None.
    """
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key or key.strip() == "":
        return None
    try:
        return Groq(api_key=key.strip())
    except Exception:
        return None

def generate_mock_recommendations(patient_dict, risk_score, risk_category, risk_drivers):
    """Generate structured high-quality clinical recommendations inside sub-sections (max 4 bullets each)."""
    bmi = patient_dict.get('bmi', 22.0)
    systolic = patient_dict.get('systolic_bp', 120)
    diastolic = patient_dict.get('diastolic_bp', 80)
    glucose = patient_dict.get('glucose', 90)
    cholesterol = patient_dict.get('cholesterol', 180)
    smoking = patient_dict.get('smoking_status', 'Non-Smoker')
    alcohol = patient_dict.get('alcohol_consumption', 'None')
    activity = patient_dict.get('physical_activity', 'High')
    
    # Primary driver check
    primary_driver = "general"
    if risk_drivers and len(risk_drivers) > 0:
        primary_driver = risk_drivers[0].get('feature', 'general').lower()
        
    # Nutrition Plan
    if 'glucose' in primary_driver or glucose >= 100:
        diet = (
            "**Foods to Eat:**\n"
            "• High-fiber vegetables (spinach, kale, broccoli) and legumes.\n"
            "• Lean proteins such as chicken breast, turkey, baked tofu, and fish.\n"
            "• Healthy fats including extra virgin olive oil, avocados, and walnuts.\n"
            "• Low-glycemic grains like steel-cut oats, quinoa, and wild rice.\n\n"
            "**Foods to Avoid:**\n"
            "• Refined sugars, sodas, fruit juices, and sweetened teas.\n"
            "• Simple starches like white bread, white rice, and pastries.\n"
            "• Ultra-processed convenience meals and high-fructose corn syrups.\n"
            "• Heavy saturated fats and trans fat spreads.\n\n"
            "**Meal Suggestions:**\n"
            "• Breakfast: Sugar-free oatmeal topped with chia seeds and blueberries.\n"
            "• Lunch: Grilled chicken breast over a bed of spinach with lemon dressing.\n"
            "• Dinner: Baked wild salmon with steamed broccoli and quinoa."
        )
    elif 'cholesterol' in primary_driver or cholesterol >= 200:
        diet = (
            "**Foods to Eat:**\n"
            "• Soluble fiber-rich foods like oats, barley, lentils, and kidney beans.\n"
            "• Foods high in Omega-3 fatty acids: salmon, walnuts, and chia seeds.\n"
            "• Phytosterol-rich options including almonds, seeds, and olive oil.\n"
            "• Plenty of antioxidant-rich fresh vegetables and cholesterol-lowering fruits.\n\n"
            "**Foods to Avoid:**\n"
            "• Saturated fats present in fatty cuts of red meat and butter.\n"
            "• Trans fats found in packaged baked goods and fried food.\n"
            "• High-cholesterol items like organ meats and full-fat dairy.\n"
            "• Heavy use of tropical oils such as coconut and palm oil.\n\n"
            "**Meal Suggestions:**\n"
            "• Breakfast: Oatmeal prepared with almond milk and raw walnuts.\n"
            "• Lunch: Mixed bean soup with a side salad drizzled with olive oil.\n"
            "• Dinner: Sautéed tofu with garlic, mushrooms, and raw vegetables."
        )
    elif 'bp' in primary_driver or 'pressure' in primary_driver or systolic >= 130:
        diet = (
            "**Foods to Eat:**\n"
            "• Potassium-rich options such as bananas, spinach, and sweet potatoes.\n"
            "• Calcium and magnesium sources: low-fat yogurt, seeds, and leafy greens.\n"
            "• Whole grains, unsalted raw nuts, and fresh berries.\n"
            "• Lean skinless poultry and fresh caught fish.\n\n"
            "**Foods to Avoid:**\n"
            "• Processed salt, soy sauce, and high-sodium seasoning packs.\n"
            "• Canned soups, cured meats (bacon, ham, cold cuts), and pickles.\n"
            "• Frozen packaged entrees and salty snack items.\n"
            "• Sugary drinks and excessive daily caffeine.\n\n"
            "**Meal Suggestions:**\n"
            "• Breakfast: Low-fat Greek yogurt topped with a sliced banana.\n"
            "• Lunch: Quinoa salad tossed with cucumber, tomatoes, and lemon juice.\n"
            "• Dinner: Roasted turkey breast with a baked sweet potato."
        )
    elif 'bmi' in primary_driver or 'weight' in primary_driver or bmi >= 25.0:
        diet = (
            "**Foods to Eat:**\n"
            "• Low-calorie density, high-fiber vegetables (cabbage, celery, zucchini).\n"
            "• Lean satiating proteins like boiled eggs, turkey breast, and white fish.\n"
            "• Small, measured portions of whole grains and seeds.\n"
            "• Raw whole apples or fresh berries as fiber-rich snacks.\n\n"
            "**Foods to Avoid:**\n"
            "• Liquid calories (sweetened coffee drinks, soda, juices, alcohol).\n"
            "• Deep-fried items, greasy fast foods, and buttered popcorn.\n"
            "• High-calorie cream-based salad dressings and mayonnaise.\n"
            "• Refined white flour bakery products.\n\n"
            "**Meal Suggestions:**\n"
            "• Breakfast: Vegetable omelet made with eggs and fresh mushrooms.\n"
            "• Lunch: Turkey roll-ups inside large lettuce wraps with mustard.\n"
            "• Dinner: Grilled cod fillet with roasted asparagus and lemon."
        )
    else:
        diet = (
            "**Foods to Eat:**\n"
            "• Balanced colorful vegetables, fresh fruits, and raw almonds.\n"
            "• Fiber-rich whole grains (farro, brown rice, whole oats) and beans.\n"
            "• Lean proteins (poultry, fish, eggs) and cold-pressed plant oils.\n"
            "• Probiotic-rich plain Greek yogurt or kefir.\n\n"
            "**Foods to Avoid:**\n"
            "• Processed sugary snacks and artificial soda drinks.\n"
            "• Deep-fried foods and heavily salted packaged chips.\n"
            "• Highly processed deli meats.\n"
            "• Trans fats and excess red meat.\n\n"
            "**Meal Suggestions:**\n"
            "• Breakfast: Whole grain toast with avocado and a poached egg.\n"
            "• Lunch: Three-bean salad with mixed greens and lemon vinaigrette.\n"
            "• Dinner: Pan-seared sea bass with sautéed kale."
        )
        
    # Exercise Plan
    if 'glucose' in primary_driver or glucose >= 100:
        exercise = (
            "**Weekly Activity Targets:**\n"
            "• Target 150 minutes of moderate-intensity cardiorespiratory exercise weekly.\n"
            "• Schedule active days (e.g. 5 days of 30 mins) to optimize insulin usage.\n"
            "• Combine with 2 sessions of strength training targeting major muscle groups.\n\n"
            "**Walking Goals:**\n"
            "• Walk briskly for 15 minutes immediately following your main meals.\n"
            "• Aim for a steady daily step target of 8,000 steps.\n\n"
            "**Cardio Recommendations:**\n"
            "• Engage in steady cycling, swimming, or elliptical training.\n"
            "• Exercise at a pace where you can comfortably converse."
        )
    elif 'bp' in primary_driver or 'pressure' in primary_driver or systolic >= 130:
        exercise = (
            "**Weekly Activity Targets:**\n"
            "• Accumulate 150 minutes of structured aerobic exercise per week.\n"
            "• Divide into 30 minutes daily on 5 days of the week.\n"
            "• Include light weight training or bodyweight resistance twice weekly.\n\n"
            "**Walking Goals:**\n"
            "• Walk at a comfortable, steady pace for 30 minutes every day.\n"
            "• Accumulate 7,500 to 10,000 steps daily.\n\n"
            "**Cardio Recommendations:**\n"
            "• Try low-impact exercises like stationary cycling or water aerobics.\n"
            "• Avoid holding your breath during exercises to prevent BP spikes."
        )
    elif 'bmi' in primary_driver or 'weight' in primary_driver or bmi >= 25.0:
        exercise = (
            "**Weekly Activity Targets:**\n"
            "• Target 150 to 250 minutes of moderate physical activity weekly.\n"
            "• Distribute activity across 5 days to support calorie expenditure.\n"
            "• Include full-body resistance training twice per week.\n\n"
            "**Walking Goals:**\n"
            "• Set a daily target of 9,000 to 10,000 walking steps.\n"
            "• Break up long desk sitting blocks with 3-minute walking intervals.\n\n"
            "**Cardio Recommendations:**\n"
            "• Choose low-impact activities: water walking, swimming, or rowing.\n"
            "• Gradually increase pace to avoid joint stress or strain."
        )
    else:
        exercise = (
            "**Weekly Activity Targets:**\n"
            "• Target 150 to 300 minutes of moderate-intensity aerobic training weekly.\n"
            "• Add strength training targeting all major muscle groups twice weekly.\n"
            "• Engage in yoga or active recovery stretching once per week.\n\n"
            "**Walking Goals:**\n"
            "• Maintain a target of 7,500 to 9,000 steps daily.\n"
            "• Climb stairs instead of riding elevators when possible.\n\n"
            "**Cardio Recommendations:**\n"
            "• Incorporate hiking, outdoor biking, swimming, or jogging.\n"
            "• Mix steady cardio with occasional interval training sessions."
        )
        
    # Lifestyle & Sleep
    lifestyle = (
        "**Sleep Guidelines:**\n"
        "• Prioritize 7-8 hours of continuous, restorative sleep nightly.\n"
        "• Go to bed and wake up at the same time every day.\n"
        "• Switch off all smartphone and TV screens 1 hour before bedtime.\n\n"
        "**Stress Management:**\n"
        "• Practice 5 minutes of slow deep box-breathing twice daily.\n"
        "• Spend at least 15 minutes in natural daylight every morning.\n"
        "• Integrate mindfulness exercises or quiet reading in the evening.\n\n"
        "**Hydration:**\n"
        "• Drink 2.0 to 2.5 liters of clean water daily.\n"
        "• Stop drinking caffeine or stimulants after 2:00 PM."
    )
    if smoking == 'Smoker':
        lifestyle += "\n• Commit to complete smoking cessation; seek NRT support."
    if alcohol == 'Heavy':
        lifestyle += "\n• Limit alcohol intake to under 1 standard drink daily or cease consumption."
        
    # Preventive Monitoring
    if 'glucose' in primary_driver or glucose >= 100:
        preventive = (
            "**Lab Tests:**\n"
            "• Fasting blood glucose and HbA1c panels every 3 to 6 months.\n"
            "• Fasting lipid panel to evaluate triglyceride-to-HDL ratios.\n"
            "• Annual comprehensive metabolic panel (CMP) to track organ parameters.\n\n"
            "**Checkup Frequency:**\n"
            "• Consult your primary care physician twice yearly to monitor trends.\n"
            "• Schedule an annual diabetic eye screening/ophthalmology exam.\n\n"
            "**Health Monitoring Schedule:**\n"
            "• Check blood glucose levels at home weekly using a glucometer.\n"
            "• Log signs of glucose fluctuation (unusual fatigue, extreme thirst)."
        )
    elif 'bp' in primary_driver or 'pressure' in primary_driver or systolic >= 130:
        preventive = (
            "**Lab Tests:**\n"
            "• Kidney function profile (eGFR, BUN, Creatinine) annually.\n"
            "• Urine analysis to monitor microalbumin levels once a year.\n"
            "• Annual screening electrocardiogram (ECG) to monitor rhythm.\n\n"
            "**Checkup Frequency:**\n"
            "• Visit a primary care doctor every 3 to 6 months for BP checks.\n"
            "• Complete an annual cardiovascular clinical risk review.\n\n"
            "**Health Monitoring Schedule:**\n"
            "• Measure blood pressure at home 2 to 3 times per week.\n"
            "• Keep a simple log of values to show your physician."
        )
    elif 'cholesterol' in primary_driver or cholesterol >= 200:
        preventive = (
            "**Lab Tests:**\n"
            "• Fasting lipid panel (Total, LDL, HDL, Triglycerides) in 3 months.\n"
            "• Consider checking advanced markers such as ApoB and hs-CRP.\n"
            "• Liver enzyme checks (AST/ALT) periodically if taking lipid medications.\n\n"
            "**Checkup Frequency:**\n"
            "• Lipid checkup with your healthcare provider every 6 months.\n"
            "• Annual cardiovascular status review with your clinician.\n\n"
            "**Health Monitoring Schedule:**\n"
            "• Schedule laboratory blood lipid panels twice per year.\n"
            "• Log dietary fiber intake and cardio exercise minutes weekly."
        )
    else:
        preventive = (
            "**Lab Tests:**\n"
            "• Routine annual screening panel (CBC, lipids, fasting glucose).\n"
            "• Annual clinical urine test and baseline metabolic check.\n"
            "• General thyroid panel (TSH) to check systemic metabolism.\n\n"
            "**Checkup Frequency:**\n"
            "• Annual comprehensive physical wellness check with a physician.\n"
            "• Bi-annual dental checkups to support cardiovascular safety.\n\n"
            "**Health Monitoring Schedule:**\n"
            "• Check blood pressure monthly at an automated kiosk or clinic.\n"
            "• Log body weight once weekly under standardized morning conditions."
        )
        
    return {
        "diet": diet,
        "exercise": exercise,
        "lifestyle": lifestyle,
        "preventive": preventive
    }

def generate_ai_recommendations(patient_dict, risk_score, risk_category, risk_drivers, api_key=None, model_id=DEFAULT_MODEL):
    """
    Generate personalized medical recommendations using Groq LLM.
    If no API key is available, falls back to a smart mock response.
    """
    client = get_groq_client(api_key)
    if not client:
        # Return mock recommendations
        return generate_mock_recommendations(patient_dict, risk_score, risk_category, risk_drivers), False
        
    # Format drivers
    drivers_str = ", ".join([f"{d['label']} (contrib: {d['contribution']}%)" for d in risk_drivers])
    
    system_prompt = (
        "You are an expert clinical health advisor. Your job is to generate highly personalized, actionable "
        "preventive health recommendations based on a screening assessment. Provide your response in a structured "
        "XML-like format with separate sections for Diet, Exercise, Lifestyle, and Preventive advice. "
        "Do not include general introduction or summaries. Use the following tags to enclose each section: "
        "<diet>...</diet>, <exercise>...</exercise>, <lifestyle>...</lifestyle>, <preventive>...</preventive>.\n"
        "Inside each tag, you MUST divide the recommendation into three specific sections using markdown bold subheadings, "
        "each having at most 4 concise, action-oriented bullet points:\n"
        "- Under <diet>, use headers: '**Foods to Eat:**', '**Foods to Avoid:**', and '**Meal Suggestions:**'\n"
        "- Under <exercise>, use headers: '**Weekly Activity Targets:**', '**Walking Goals:**', and '**Cardio Recommendations:**'\n"
        "- Under <lifestyle>, use headers: '**Sleep Guidelines:**', '**Stress Management:**', and '**Hydration:**'\n"
        "- Under <preventive>, use headers: '**Lab Tests:**', '**Checkup Frequency:**', and '**Health Monitoring Schedule:**'\n"
        "Keep the bullet points extremely brief, direct, and actionable. Avoid long paragraphs or general text."
    )
    
    user_prompt = f"""
    PATIENT PROFILE:
    - Age: {patient_dict.get('age')}
    - Gender: {patient_dict.get('gender')}
    - BMI: {patient_dict.get('bmi')} (Height: {patient_dict.get('height')} cm, Weight: {patient_dict.get('weight')} kg)
    - Blood Pressure: {patient_dict.get('systolic_bp')}/{patient_dict.get('diastolic_bp')} mmHg
    - Fasting Glucose: {patient_dict.get('glucose')} mg/dL
    - Cholesterol: {patient_dict.get('cholesterol')} mg/dL
    - Smoking Status: {patient_dict.get('smoking_status')}
    - Alcohol Consumption: {patient_dict.get('alcohol_consumption')}
    - Physical Activity: {patient_dict.get('physical_activity')}
    - Family Medical History: {patient_dict.get('family_history')}
    
    SCREENING METRICS:
    - Calculated Risk Score: {risk_score}%
    - Calculated Risk Category: {risk_category}
    - Key Risk Drivers: {drivers_str}
    
    Generate tailored clinical recommendations following the requested formatting rules.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model_id,
            temperature=0.2,
            max_tokens=1000
        )
        response_text = chat_completion.choices[0].message.content
        
        # Parse XML tags
        def extract_section(tag, text):
            match = re.search(fr'<{tag}>(.*?)</{tag}>', text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else "No recommendations generated."

        parsed_recommendations = {
            "diet": extract_section("diet", response_text),
            "exercise": extract_section("exercise", response_text),
            "lifestyle": extract_section("lifestyle", response_text),
            "preventive": extract_section("preventive", response_text)
        }
        
        # If parsing failed and we got plain text, fallback
        if all(val == "No recommendations generated." for val in parsed_recommendations.values()):
            return generate_mock_recommendations(patient_dict, risk_score, risk_category, risk_drivers), False
            
        return parsed_recommendations, True
        
    except Exception as e:
        print(f"Groq API Error: {str(e)}")
        return generate_mock_recommendations(patient_dict, risk_score, risk_category, risk_drivers), False

def get_ai_chat_response(messages, patient_context, api_key=None, model_id=DEFAULT_MODEL):
    """
    Handle a user chatbot message.
    Grounds the chatbot using patient context.
    """
    client = get_groq_client(api_key)
    
    # Patient Context String
    patient_str = f"""
    Patient Context:
    - Name: {patient_context.get('name', 'Anonymous')}
    - Age: {patient_context.get('age')}
    - Gender: {patient_context.get('gender')}
    - BMI: {patient_context.get('bmi')}
    - Blood Pressure: {patient_context.get('systolic_bp')}/{patient_context.get('diastolic_bp')} mmHg
    - Glucose: {patient_context.get('glucose')} mg/dL
    - Cholesterol: {patient_context.get('cholesterol')} mg/dL
    - Smoking: {patient_context.get('smoking_status')}
    - Alcohol: {patient_context.get('alcohol_consumption')}
    - Activity Level: {patient_context.get('physical_activity')}
    - Family History: {patient_context.get('family_history')}
    - Predicted Risk Score: {patient_context.get('risk_score')}%
    - Predicted Risk Category: {patient_context.get('risk_category')}
    - Key Risk Drivers: {patient_context.get('risk_drivers_str', 'None')}
    
    Risk Improvement Simulator (Goals):
    - Simulator Current Weight: {patient_context.get('current_logged_weight')} kg, Goal: {patient_context.get('goal_weight')} kg
    - Simulator Current Glucose: {patient_context.get('current_logged_glucose')} mg/dL, Goal: {patient_context.get('goal_glucose')} mg/dL
    - Simulator Current BP: {patient_context.get('current_logged_sys_bp')} mmHg (Sys), Goal: {patient_context.get('goal_systolic_bp')} mmHg
    - Current Calculated Risk: {patient_context.get('risk_score')}%
    - Simulator Projected Risk: {patient_context.get('projected_risk')}%
    - Simulator Risk Reduction: {patient_context.get('risk_reduction')}%
    
    Assessment Timeline History:
    - History: {patient_context.get('timeline_history_str', 'No previous history available')}
    - Overall Trend: {patient_context.get('overall_trend_status', 'Stable')}
    """
    
    system_prompt = (
        "You are an AI Health Assistant part of a Clinical Health Risk Predictor application. "
        "Your role is to help patients interpret their screening results, explain why their risk score is high/moderate/low, "
        "and provide educational insights on how they can improve their markers (like cholesterol, blood pressure, glucose, BMI). "
        "Always ground your responses in the patient's specific details and simulator targets provided in the context below. "
        "Keep your advice supportive, clear, structured, and clinically sound. "
        "Do not write excessive paragraphs; structure replies with bullet points where appropriate. "
        "Always add a medical disclaimer that you are an AI assistant and they should consult a real medical doctor for diagnosis. "
        "\n\n"
        f"{patient_str}"
    )
    
    if not client:
        # Mock chatbot response
        last_user_message = messages[-1]['content'].lower()
        
        if "can i eat rice" in last_user_message:
            return (
                "Based on your clinical profile, white rice has a high glycemic index and can cause rapid spikes in blood sugar. "
                "Since your glucose level is recorded as "
                f"{patient_context.get('glucose')} mg/dL, it is recommended to substitute white rice with whole grain alternatives "
                "such as brown rice, wild rice, quinoa, or cauliflower rice, and strictly monitor portion sizes to maintain glycemic stability.\n\n"
                "*Disclaimer: Educational guidance only. This assistant does not replace professional medical advice.*"
            )
        elif "lower glucose naturally" in last_user_message or "reduce glucose" in last_user_message:
            return (
                "To lower your fasting glucose naturally, focus on the following core areas:\n"
                "1. **Post-Meal Walking:** Engage in 15 minutes of brisk walking immediately after your main meals to enhance muscular glucose uptake.\n"
                "2. **Glycemic Diet Control:** Emphasize high-soluble fiber, lean protein, and complex grains. Restrict refined flour and sugary sodas.\n"
                "3. **Weight & BMI Reduction:** Lowering your weight (your simulator target is "
                f"{patient_context.get('goal_weight')} kg) improves general insulin sensitivity.\n"
                "4. **Sleep & Stress:** Maintain 7-8 hours of sleep. Elevated cortisol from sleep deficit triggers gluconeogenesis and increases insulin resistance.\n\n"
                "*Disclaimer: Educational guidance only. This assistant does not replace professional medical advice.*"
            )
        elif "causes high cholesterol" in last_user_message or "cholesterol" in last_user_message:
            return (
                "High cholesterol is typically caused by a combination of factors:\n"
                "• **Dietary Lipids:** Diets rich in saturated fats (red meat, full-fat dairy) and trans fats increase LDL cholesterol levels.\n"
                "• **Sedentary Lifestyle:** A lack of physical activity reduces HDL (good) cholesterol and slows down lipid metabolism.\n"
                "• **Genetic Factors:** A family history of cardiovascular disease or hyperlipidemia often impacts hepatic lipid clearance.\n"
                "• **Systemic Factors:** Age and baseline BMI are contributing metabolic drivers.\n\n"
                f"Your current cholesterol is {patient_context.get('cholesterol')} mg/dL. We recommend reducing saturated fats and increasing soluble fiber.\n\n"
                "*Disclaimer: Educational guidance only. This assistant does not replace professional medical advice.*"
            )
        elif "reduce blood pressure" in last_user_message or "lower bp" in last_user_message or "pressure" in last_user_message:
            return (
                f"Your blood pressure is currently {patient_context.get('systolic_bp')}/{patient_context.get('diastolic_bp')} mmHg. "
                f"Your simulator target is {patient_context.get('goal_systolic_bp')} mmHg systolic. To reduce it naturally:\n"
                "1. **Adopt the DASH Diet:** Reduce sodium intake below 1,500 mg per day, and increase potassium, magnesium, and calcium.\n"
                "2. **Structured Aerobic Exercise:** Commit to 150 minutes of moderate cardio (brisk walking, stationary cycling) weekly.\n"
                "3. **Limit Alcohol & Cessation:** Restrict alcohol and completely cease smoking, which causes immediate arterial stiffness.\n"
                "4. **Manage Chronic Stress:** Implement daily deep-breathing exercises or box-breathing to reduce sympathetic nervous system tone.\n\n"
                "*Disclaimer: Educational guidance only. This assistant does not replace professional medical advice.*"
            )
        elif "why" in last_user_message or "risk" in last_user_message:
            return (
                f"Your current assessment places you in the **{patient_context.get('risk_category')}** category with a score of **"
                f"{patient_context.get('risk_score')}%**. Your primary risk concern is: {patient_context.get('risk_drivers_str')}. "
                "By adjusting parameters in the Risk Simulator (such as reaching your weight goal of "
                f"{patient_context.get('goal_weight')} kg), you can lower your risk down to {patient_context.get('projected_risk')}%, "
                f"resulting in a {patient_context.get('risk_reduction')}% risk reduction.\n\n"
                "*Disclaimer: Educational guidance only. This assistant does not replace professional medical advice.*"
            )
        else:
            return (
                f"Hello! I am your AI Health Assistant. I see that your current risk category is {patient_context.get('risk_category')} ("
                f"{patient_context.get('risk_score')}%). You can ask me questions such as 'How can I lower glucose naturally?' or 'What causes high cholesterol?' "
                "grounded directly in your biomarkers.\n\n"
                "*Disclaimer: Educational guidance only. This assistant does not replace professional medical advice.*"
            )

    # Prepare messages payload
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
        
    try:
        chat_completion = client.chat.completions.create(
            messages=api_messages,
            model=model_id,
            temperature=0.4,
            max_tokens=600
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI Chatbot Error: {str(e)}. Please check your API key and network connection."
