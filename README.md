# 🏥 Health Risk Predictor

An AI-powered healthcare application that predicts cardiovascular and metabolic health risks using a **Random Forest Machine Learning model**. The platform analyzes patient health data, provides AI-powered insights, generates personalized health recommendations, and creates downloadable PDF health reports.

---

## 🌟 Features

- Patient health assessment form
- Health risk prediction using Machine Learning
- AI-powered health insights using the Groq API
- Random Forest–based risk classification
- Explainable risk analysis
- Personalized health recommendations
- Interactive health dashboard
- Downloadable PDF health reports

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python

### Machine Learning
- Scikit-learn
- Random Forest Classifier

### AI
- Groq API
- Llama 3.3 70B Model
- Prompt Engineering

### Visualization
- Plotly

### PDF Generation
- ReportLab

### Other Libraries
- Pandas
- NumPy

---

## 📂 Project Structure

```text
Health-Risk-Predictor/
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── app.py
├── ai_helper.py
├── ml_model.py
├── ocr_helper.py
├── report_generator.py
├── model.joblib
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Bhagyashree2310/Health-Risk-Predictor.git
cd Health-Risk-Predictor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` File

```env
GROQ_API_KEY=your_api_key_here
```

### 4. Run the Application

```bash
python app.py
```

---

## 🚀 Workflow

1. Enter patient health details.
2. The system preprocesses the input data.
3. The Random Forest model predicts the patient's health risk.
4. The Groq LLM analyzes the prediction and generates personalized health insights.
5. A downloadable PDF health report is generated.

---

## 🎯 Use Cases

- Preventive healthcare screening
- Early disease risk assessment
- Personalized health recommendations
- Clinical decision support
- Patient health monitoring

---

## 📄 Output

The application generates:

- Health Risk Category (Low, Medium, High)
- Risk Score
- AI-powered Health Insights
- Personalized Recommendations
- Downloadable PDF Health Report

---

## 🔮 Future Enhancements

- Patient login and authentication
- Doctor dashboard
- Patient history tracking
- Health trend visualization
- Wearable device integration
- Email reminders and follow-up notifications
