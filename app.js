document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // DOM Element Selections
    // -------------------------------------------------------------
    
    // Navigation Pills
    const navPills = document.querySelectorAll(".nav-pill");
    const tabViews = document.querySelectorAll(".tab-view");
    const tabInsightsBtn = document.getElementById("tab-insights-btn");
    const tabActionplanBtn = document.getElementById("tab-actionplan-btn");

    // Form inputs (Patient info & Clinical indicators)
    const patientName = document.getElementById("patient-name");
    const patientGender = document.getElementById("patient-gender");
    const patientAge = document.getElementById("patient-age");
    const patientHeight = document.getElementById("patient-height");
    const patientWeight = document.getElementById("patient-weight");
    const patientSysBp = document.getElementById("patient-sys-bp");
    const patientDiaBp = document.getElementById("patient-dia-bp");
    const patientGlucose = document.getElementById("patient-glucose");
    const patientCholesterol = document.getElementById("patient-cholesterol");
    const patientFamilyHist = document.getElementById("patient-family-hist");
    const patientSmoking = document.getElementById("patient-smoking");
    const patientAlcohol = document.getElementById("patient-alcohol");
    const patientActivity = document.getElementById("patient-activity");

    // BMI Card Elements
    const bmiKpiCard = document.getElementById("bmi-kpi-card");
    const bmiValue = document.getElementById("bmi-value");
    const bmiStatus = document.getElementById("bmi-status");

    // Validation alert
    const validationAlert = document.getElementById("validation-alert");
    const validationFieldsList = document.getElementById("validation-fields-list");

    // Control buttons
    const btnAnalyze = document.getElementById("btn-analyze");
    const btnReset = document.getElementById("btn-reset");

    // Upload & Mock Scenarios
    const fileUploader = document.getElementById("file-uploader");
    const uploadDropzone = document.getElementById("upload-dropzone");
    const uploadStatusBox = document.getElementById("upload-status-box");
    const statusFilename = document.getElementById("status-filename");
    const statusBadge = document.getElementById("status-badge");
    const statusText = document.getElementById("status-text");
    const statusMetricsCount = document.getElementById("status-metrics-count");
    const mockScenarioBtns = document.querySelectorAll(".mock-scenario-btn");
    const ocrTextLength = document.getElementById("ocr-text-length");
    const ocrAvgConfidence = document.getElementById("ocr-avg-confidence");
    const reviewTableBody = document.getElementById("review-table-body");
    const btnUseExtracted = document.getElementById("btn-use-extracted");
    const rawOcrText = document.getElementById("raw-ocr-text");
    const reviewTableContainer = document.getElementById("review-table-container");

    // Insights tab elements
    const riskSummaryBanner = document.getElementById("risk-summary-banner");
    const bannerCategory = document.getElementById("banner-category");
    const bannerScore = document.getElementById("banner-score");
    const bannerDriver = document.getElementById("banner-driver");
    const bannerPlan = document.getElementById("banner-plan");
    const execSummaryContent = document.getElementById("exec-summary-content");
    const shapChartContainer = document.getElementById("shap-chart-container");
    const recommendedActionsList = document.getElementById("recommended-actions-list");
    const clinicalInterpretationList = document.getElementById("clinical-interpretation-list");

    // Action plan elements
    const interventionPriority = document.getElementById("intervention-priority");
    const kpiTargetName = document.getElementById("kpi-target-name");
    const kpiCurrentVal = document.getElementById("kpi-current-val");
    const kpiTargetVal = document.getElementById("kpi-target-val");
    const kpiOutcome = document.getElementById("kpi-outcome");
    const kpiTimeline = document.getElementById("kpi-timeline");

    const nutritionBulletsList = document.getElementById("nutrition-bullets-list");
    const activityBulletsList = document.getElementById("activity-bullets-list");
    const monitoringBulletsList = document.getElementById("monitoring-bullets-list");

    // Chatbot elements
    const chatLogsArea = document.getElementById("chat-logs-area");
    const chatInput = document.getElementById("chat-input");
    const btnChatSend = document.getElementById("btn-chat-send");
    const suggestedPillsContainer = document.getElementById("suggested-pills-container");

    // Export element
    const btnExportPdf = document.getElementById("btn-export-pdf");

    // -------------------------------------------------------------
    // Global Application State
    // -------------------------------------------------------------
    let currentAnalysisResult = null;
    let pendingExtractedParameters = null;
    let chatHistory = [
        {
            role: "assistant",
            content: "Hello! I am your AI Health Assistant. I see your analysis details and priority targets. How can I help you interpret your metrics or recommendations today?"
        }
    ];

    // List of form inputs to watch and persist
    const formInputElements = [
        patientName, patientGender, patientAge, patientHeight, patientWeight,
        patientSysBp, patientDiaBp, patientGlucose, patientCholesterol,
        patientFamilyHist, patientSmoking, patientAlcohol, patientActivity
    ];

    // -------------------------------------------------------------
    // Initialization & State Persistence Restoration
    // -------------------------------------------------------------
    function init() {
        restoreInputsFromLocalStorage();
        calculateBMI();
        
        // Restore last analysis result if present
        const savedResult = localStorage.getItem("last_analysis_result");
        if (savedResult) {
            try {
                currentAnalysisResult = JSON.parse(savedResult);
                enableNavigationPills();
                renderInsightsPage(currentAnalysisResult);
                renderActionPlanPage(currentAnalysisResult);
            } catch (e) {
                console.error("Failed to parse saved analysis result", e);
                localStorage.removeItem("last_analysis_result");
            }
        }
        
        // Restore chat logs if present
        const savedChat = localStorage.getItem("chat_history");
        if (savedChat) {
            try {
                chatHistory = JSON.parse(savedChat);
                renderChatHistory();
            } catch (e) {
                console.error("Failed to parse saved chat history", e);
                localStorage.removeItem("chat_history");
            }
        }

        // Restore file upload status if present
        const savedUpload = localStorage.getItem("upload_status");
        if (savedUpload) {
            try {
                const uploadData = JSON.parse(savedUpload);
                uploadStatusBox.classList.remove("hidden");
                statusFilename.textContent = uploadData.filename;
                statusText.textContent = uploadData.statusText;
                statusMetricsCount.textContent = uploadData.metricsText;
            } catch (e) {
                console.error("Failed to parse saved upload data", e);
            }
        }
        
        // Initialize missing info panel
        updateMissingInfoPanel();
    }

    // Save current inputs to localStorage
    function saveInputsToLocalStorage() {
        formInputElements.forEach(elem => {
            if (elem) {
                localStorage.setItem(`input_${elem.id}`, elem.value);
            }
        });
    }

    // Restore inputs from localStorage
    function restoreInputsFromLocalStorage() {
        formInputElements.forEach(elem => {
            if (elem) {
                const val = localStorage.getItem(`input_${elem.id}`);
                if (val !== null) {
                    elem.value = val;
                }
            }
        });
    }

    // Listen to changes on all inputs to automatically persist them
    formInputElements.forEach(elem => {
        if (elem) {
            elem.addEventListener("input", () => {
                saveInputsToLocalStorage();
                elem.style.border = "";
                if (elem.id === "patient-height" || elem.id === "patient-weight") {
                    calculateBMI();
                }
                updateMissingInfoPanel();
            });
            elem.addEventListener("change", () => {
                saveInputsToLocalStorage();
                elem.style.border = "";
                if (elem.id === "patient-height" || elem.id === "patient-weight") {
                    calculateBMI();
                }
                updateMissingInfoPanel();
            });
        }
    });

    // -------------------------------------------------------------
    // Live BMI Calculations
    // -------------------------------------------------------------
    function calculateBMI() {
        const heightVal = parseFloat(patientHeight.value);
        const weightVal = parseFloat(patientWeight.value);

        // Reset classes
        bmiKpiCard.className = "bmi-kpi-card";

        if (heightVal > 0 && weightVal > 0) {
            const heightM = heightVal / 100;
            const bmi = weightVal / (heightM * heightM);
            const roundedBmi = bmi.toFixed(1);

            bmiValue.textContent = roundedBmi;
            bmiStatus.classList.remove("hidden");

            if (bmi < 18.5) {
                bmiKpiCard.classList.add("bmi-blue");
                bmiStatus.innerHTML = "🔵 Underweight";
            } else if (bmi >= 18.5 && bmi < 25) {
                bmiKpiCard.classList.add("bmi-green");
                bmiStatus.innerHTML = "🟢 Healthy";
            } else if (bmi >= 25 && bmi < 30) {
                bmiKpiCard.classList.add("bmi-orange");
                bmiStatus.innerHTML = "🟠 Overweight";
            } else {
                bmiKpiCard.classList.add("bmi-red");
                bmiStatus.innerHTML = "🔴 Obese";
            }
        } else {
            // Muted Empty State
            bmiValue.textContent = "--";
            bmiStatus.innerHTML = "";
            bmiStatus.classList.add("hidden");
            bmiKpiCard.classList.add("bmi-muted");
        }
    }

    // -------------------------------------------------------------
    // SPA Tab Navigation
    // -------------------------------------------------------------
    navPills.forEach(pill => {
        pill.addEventListener("click", () => {
            if (pill.hasAttribute("disabled")) return;

            const targetTab = pill.getAttribute("data-tab");

            // Update nav pills status
            navPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");

            // Update tab contents view
            tabViews.forEach(view => {
                view.classList.remove("active");
                if (view.id === `${targetTab}-tab`) {
                    view.classList.add("active");
                }
            });

            // Scroll to top
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    });

    function navigateToTab(tabName) {
        const targetPill = document.querySelector(`.nav-pill[data-tab="${tabName}"]`);
        if (targetPill) {
            targetPill.removeAttribute("disabled");
            targetPill.click();
        }
    }

    function enableNavigationPills() {
        tabInsightsBtn.removeAttribute("disabled");
        tabActionplanBtn.removeAttribute("disabled");
    }

    function disableNavigationPills() {
        tabInsightsBtn.setAttribute("disabled", "true");
        tabActionplanBtn.setAttribute("disabled", "true");
    }

    // -------------------------------------------------------------
    // File Extraction Review & Confirmation Workflow
    // -------------------------------------------------------------
    uploadDropzone.addEventListener("click", () => {
        fileUploader.click();
    });

    // Handle drag events
    ["dragenter", "dragover"].forEach(eventName => {
        uploadDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        uploadDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadDropzone.classList.remove("dragover");
        }, false);
    });

    uploadDropzone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    fileUploader.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    function clearInputs() {
        formInputElements.forEach(elem => {
            if (elem) {
                if (elem.tagName === "SELECT") {
                    elem.value = "Select";
                } else {
                    elem.value = "";
                }
                elem.style.border = "";
            }
        });
        calculateBMI();
        
        // Hide dynamic panels and summary card
        const extPanel = document.getElementById("extracted-biomarkers-panel");
        const missPanel = document.getElementById("missing-info-panel");
        const summaryCard = document.getElementById("report-summary-card");
        const warningBanner = document.getElementById("ocr-warning-banner");
        
        if (extPanel) extPanel.style.display = "none";
        if (missPanel) missPanel.style.display = "none";
        if (summaryCard) summaryCard.style.display = "none";
        if (warningBanner) warningBanner.classList.add("hidden");
    }

    function updateMissingInfoPanel() {
        const missingPanel = document.getElementById("missing-info-panel");
        const missingList = document.getElementById("missing-info-list");
        if (!missingPanel || !missingList) return;

        const missing = [];
        if (!patientAge.value) missing.push("Age");
        if (!patientHeight.value) missing.push("Height");
        if (!patientWeight.value) missing.push("Weight");
        if (!patientSysBp.value || !patientDiaBp.value) missing.push("Blood Pressure");
        if (!patientGlucose.value) missing.push("Blood Glucose");
        if (!patientCholesterol.value) missing.push("Cholesterol");
        
        if (patientSmoking.value === "Select") missing.push("Smoking Status");
        if (patientAlcohol.value === "Select") missing.push("Alcohol Consumption");
        if (patientActivity.value === "Select") missing.push("Physical Activity");
        if (patientFamilyHist.value === "Select") missing.push("Family History");

        if (missing.length > 0) {
            missingPanel.style.display = "block";
            missingList.innerHTML = missing.map(item => `<li style="margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><i class="fa-solid fa-circle" style="font-size: 0.4rem; color: #EF4444;"></i> ${item}</li>`).join("");
            
            const summaryMissing = document.getElementById("summary-missing-inputs");
            if (summaryMissing) {
                summaryMissing.textContent = missing.join(", ");
                summaryMissing.style.color = "#EF4444";
            }
        } else {
            missingPanel.style.display = "none";
            const summaryMissing = document.getElementById("summary-missing-inputs");
            if (summaryMissing) {
                summaryMissing.textContent = "None";
                summaryMissing.style.color = "#10B981";
            }
        }
    }

    function handleFileUpload(file) {
        // Clear inputs first to prevent leftover mock profiles
        clearInputs();

        const formData = new FormData();
        formData.append("file", file);

        // Show loading status
        uploadStatusBox.classList.remove("hidden");
        statusFilename.textContent = file.name;
        statusText.textContent = "Status: Uploading and extracting...";
        statusMetricsCount.textContent = "";
        
        // Hide review details while loading
        reviewTableContainer.style.display = "none";
        btnUseExtracted.style.display = "none";
        ocrTextLength.textContent = "0 chars";
        ocrAvgConfidence.textContent = "0%";
        rawOcrText.textContent = "";

        fetch("/api/upload", {
            method: "POST",
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to process document");
            }
            return response.json();
        })
        .then(data => {
            displayExtractionReview(data);
        })
        .catch(err => {
            console.error(err);
            statusText.textContent = "Status: Extraction Failed";
            statusMetricsCount.textContent = err.message || "Failed to process document due to a network or server error.";
            pendingExtractedParameters = null;
            reviewTableContainer.style.display = "none";
            btnUseExtracted.style.display = "none";
        });
    }

    // Mock scenario clicks (GET request to dedicated simulated scenario endpoint)
    mockScenarioBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            // Clear inputs first
            clearInputs();

            const filename = btn.getAttribute("data-filename");
            
            uploadStatusBox.classList.remove("hidden");
            statusFilename.textContent = filename;
            statusText.textContent = "Status: Fetching mock scenario data...";
            statusMetricsCount.textContent = "";

            reviewTableContainer.style.display = "none";
            btnUseExtracted.style.display = "none";
            ocrTextLength.textContent = "0 chars";
            ocrAvgConfidence.textContent = "0%";
            rawOcrText.textContent = "";

            fetch(`/api/mock_scenario/${filename}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Mock scenario fetch failed");
                }
                return response.json();
            })
            .then(data => {
                displayExtractionReview(data);
            })
            .catch(err => {
                console.error(err);
                statusText.textContent = "Status: Simulated Extraction Failed";
                statusMetricsCount.textContent = err.message || "Failed to load mock scenario details.";
                pendingExtractedParameters = null;
            });
        });
    });

    function displayExtractionReview(data) {
        const warningBanner = document.getElementById("ocr-warning-banner");
        
        if (data.success && data.parameters && data.parameters.length > 0) {
            const ocrConf = data.ocr_confidence !== undefined ? data.ocr_confidence : 98.0;
            
            // Check confidence warning (< 50%)
            if (ocrConf < 50.0) {
                statusText.textContent = "Status: Low Confidence Warning";
                statusMetricsCount.textContent = "Low OCR confidence detected. Please upload a clearer report or manually verify values.";
                
                if (warningBanner) warningBanner.classList.remove("hidden");
                
                pendingExtractedParameters = null;
                reviewTableContainer.style.display = "none";
                btnUseExtracted.style.display = "none";
                
                // Hide dynamic panels and card
                document.getElementById("extracted-biomarkers-panel").style.display = "none";
                document.getElementById("missing-info-panel").style.display = "none";
                document.getElementById("report-summary-card").style.display = "none";
                
                // Metadata display
                const rawText = data.text || "";
                ocrTextLength.textContent = `${rawText.length} chars`;
                ocrAvgConfidence.textContent = `${Math.round(ocrConf)}%`;
                rawOcrText.textContent = rawText || "No raw text available.";
                return;
            }
            
            if (warningBanner) warningBanner.classList.add("hidden");
            
            statusText.textContent = "Status: Successful";
            statusMetricsCount.textContent = `Successfully extracted ${data.metrics_count} clinical biomarkers.`;
            
            // Show review block
            reviewTableContainer.style.display = "block";
            btnUseExtracted.style.display = "block";
            btnUseExtracted.disabled = false;
            btnUseExtracted.innerHTML = '<i class="fa-solid fa-square-check"></i> Use Extracted Values';

            // Store pending parameters in global state
            pendingExtractedParameters = data.parameters;

            // Render table rows
            reviewTableBody.innerHTML = "";
            let sumConfidence = 0;
            let countConfidence = 0;

            data.parameters.forEach(param => {
                const tr = document.createElement("tr");
                tr.style.borderBottom = "1px solid #F1F5F9";
                
                const confVal = parseInt(param.confidence) || 0;
                sumConfidence += confVal;
                countConfidence++;
                
                let badgeColor = "var(--accent-green)";
                if (confVal < 92) {
                    badgeColor = "var(--accent-orange)";
                }

                tr.innerHTML = `
                    <td style="padding: 8px 4px; font-weight: 600; color: var(--text-dark);">${param.name}</td>
                    <td style="padding: 8px 4px; color: var(--primary-color); font-weight: 700;">${param.value}</td>
                    <td style="padding: 8px 4px; text-align: right; font-weight: 700; color: ${badgeColor};">${param.confidence}</td>
                `;
                reviewTableBody.appendChild(tr);
            });

            // Metadata display
            const rawText = data.text || "";
            ocrTextLength.textContent = `${rawText.length} chars`;
            ocrAvgConfidence.textContent = `${Math.round(ocrConf)}%`;
            rawOcrText.textContent = rawText || "No raw text available.";
            
            // Render dynamic panels
            const biomarkersList = document.getElementById("extracted-biomarkers-list");
            if (biomarkersList) {
                biomarkersList.innerHTML = "";
                let countBiomarkers = 0;
                data.parameters.forEach(param => {
                    if (param.value !== undefined && param.value !== null && param.value.toString().trim() !== "") {
                        const li = document.createElement("li");
                        li.style.marginBottom = "4px";
                        li.style.display = "flex";
                        li.style.alignItems = "center";
                        li.style.gap = "6px";
                        li.innerHTML = `<i class="fa-solid fa-check" style="color: #10B981; font-weight: bold;"></i> <strong>${param.name}:</strong> ${param.value}`;
                        biomarkersList.appendChild(li);
                        countBiomarkers++;
                    }
                });
                if (countBiomarkers > 0) {
                    document.getElementById("extracted-biomarkers-panel").style.display = "block";
                }
            }

            // Update Report Summary Card details
            const nameParam = data.parameters.find(p => p.field === 'patient-name');
            const ageParam = data.parameters.find(p => p.field === 'patient-age');
            const genderParam = data.parameters.find(p => p.field === 'patient-gender');
            
            document.getElementById("summary-patient-name").textContent = nameParam ? nameParam.value : "Anonymous";
            document.getElementById("summary-patient-age-gender").textContent = (ageParam ? ageParam.value : "--") + " / " + (genderParam ? genderParam.value : "--");
            document.getElementById("summary-biomarkers-count").textContent = data.metrics_count;
            document.getElementById("summary-ocr-confidence").textContent = Math.round(ocrConf) + "%";
            document.getElementById("report-summary-card").style.display = "block";

            // Update Missing Info dynamic panel
            updateMissingInfoPanel();

            // Persist the status in localStorage
            localStorage.setItem("upload_status", JSON.stringify({
                filename: data.filename,
                statusText: "Status: Successful",
                metricsText: `Successfully extracted ${data.metrics_count} clinical biomarkers.`
            }));
        } else {
            statusText.textContent = "Status: Failed";
            const errorMsg = data.error || "No valid clinical parameters could be extracted from this report.";
            statusMetricsCount.textContent = errorMsg;
            pendingExtractedParameters = null;

            if (warningBanner) warningBanner.classList.add("hidden");

            // Hide review elements
            reviewTableContainer.style.display = "none";
            btnUseExtracted.style.display = "none";
            ocrTextLength.textContent = "0 chars";
            ocrAvgConfidence.textContent = "0%";
            rawOcrText.textContent = data.text || errorMsg;

            document.getElementById("extracted-biomarkers-panel").style.display = "none";
            document.getElementById("missing-info-panel").style.display = "none";
            document.getElementById("report-summary-card").style.display = "none";
        }
    }

    // Confirm button: Apply values to Form inputs
    btnUseExtracted.addEventListener("click", () => {
        if (!pendingExtractedParameters || pendingExtractedParameters.length === 0) {
            alert("No extracted parameters available to apply.");
            return;
        }

        let appliedCount = 0;
        pendingExtractedParameters.forEach(param => {
            if (param.field) {
                const inputElem = document.getElementById(param.field);
                if (inputElem) {
                    inputElem.value = param.value;
                    appliedCount++;
                }
            }
        });

        // Trigger updates & save state
        calculateBMI();
        saveInputsToLocalStorage();
        updateMissingInfoPanel();

        // Visual feedback
        btnUseExtracted.innerHTML = `<i class="fa-solid fa-circle-check"></i> Applied ${appliedCount} Parameters!`;
        btnUseExtracted.disabled = true;
        
        setTimeout(() => {
            btnUseExtracted.innerHTML = '<i class="fa-solid fa-square-check"></i> Use Extracted Values';
            btnUseExtracted.disabled = false;
        }, 1500);
    });

    // -------------------------------------------------------------
    // Reset Profile Action
    // -------------------------------------------------------------
    btnReset.addEventListener("click", () => {
        // Reset all inputs to blank/default
        patientName.value = "";
        patientGender.value = "Select";
        patientAge.value = "";
        patientHeight.value = "";
        patientWeight.value = "";
        patientSysBp.value = "";
        patientDiaBp.value = "";
        patientGlucose.value = "";
        patientCholesterol.value = "";
        patientFamilyHist.value = "Select";
        patientSmoking.value = "Select";
        patientAlcohol.value = "Select";
        patientActivity.value = "Select";

        // Remove red borders
        formInputElements.forEach(elem => {
            if (elem) elem.style.border = "";
        });

        // Reset file uploader
        fileUploader.value = "";
        uploadStatusBox.classList.add("hidden");

        // Hide dynamic panels and summary card
        const extPanel = document.getElementById("extracted-biomarkers-panel");
        const missPanel = document.getElementById("missing-info-panel");
        const summaryCard = document.getElementById("report-summary-card");
        const warningBanner = document.getElementById("ocr-warning-banner");
        
        if (extPanel) extPanel.style.display = "none";
        if (missPanel) missPanel.style.display = "none";
        if (summaryCard) summaryCard.style.display = "none";
        if (warningBanner) warningBanner.classList.add("hidden");

        // Recalculate BMI
        calculateBMI();

        // Clear local storage fields
        localStorage.clear();

        // Disable tabs & Reset current analysis result
        disableNavigationPills();
        currentAnalysisResult = null;

        // Reset Chat
        chatHistory = [
            {
                role: "assistant",
                content: "Hello! I am your AI Health Assistant. I see your analysis details and priority targets. How can I help you interpret your metrics or recommendations today?"
            }
        ];
        renderChatHistory();

        // Hide validation alerts
        validationAlert.classList.add("hidden");

        // Go to assessment tab
        navigateToTab("assessment");
    });

    // -------------------------------------------------------------
    // Analyze Risk Action
    // -------------------------------------------------------------
    btnAnalyze.addEventListener("click", () => {
        validationAlert.classList.add("hidden");

        // Clear previous red borders
        formInputElements.forEach(elem => {
            if (elem) elem.style.border = "";
        });

        // Validation list
        const missingFields = [];
        if (!patientAge.value) { missingFields.push("Age"); patientAge.style.border = "2px solid #EF4444"; }
        if (!patientHeight.value) { missingFields.push("Height"); patientHeight.style.border = "2px solid #EF4444"; }
        if (!patientWeight.value) { missingFields.push("Weight"); patientWeight.style.border = "2px solid #EF4444"; }
        if (!patientSysBp.value) { missingFields.push("Systolic BP"); patientSysBp.style.border = "2px solid #EF4444"; }
        if (!patientDiaBp.value) { missingFields.push("Diastolic BP"); patientDiaBp.style.border = "2px solid #EF4444"; }
        if (!patientGlucose.value) { missingFields.push("Blood Glucose"); patientGlucose.style.border = "2px solid #EF4444"; }
        if (!patientCholesterol.value) { missingFields.push("Cholesterol"); patientCholesterol.style.border = "2px solid #EF4444"; }

        if (missingFields.length > 0) {
            validationFieldsList.textContent = "Additional patient information is required before risk assessment can be generated.";
            validationAlert.classList.remove("hidden");
            window.scrollTo({ top: validationAlert.offsetTop - 20, behavior: "smooth" });
            return;
        }

        // Collect request payload
        const payload = {
            name: patientName.value || "Anonymous",
            age: parseInt(patientAge.value),
            gender: patientGender.value,
            height: parseFloat(patientHeight.value),
            weight: parseFloat(patientWeight.value),
            systolic_bp: parseInt(patientSysBp.value),
            diastolic_bp: parseInt(patientDiaBp.value),
            glucose: parseFloat(patientGlucose.value),
            cholesterol: parseFloat(patientCholesterol.value),
            smoking_status: patientSmoking.value,
            alcohol_consumption: patientAlcohol.value,
            physical_activity: patientActivity.value,
            family_history: patientFamilyHist.value
        };

        btnAnalyze.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing patient risk...';
        btnAnalyze.disabled = true;

        fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Analysis request failed");
            }
            return response.json();
        })
        .then(data => {
            btnAnalyze.innerHTML = '<i class="fa-solid fa-heart-pulse"></i> Analyze Patient Risk';
            btnAnalyze.disabled = false;

            if (data.success) {
                currentAnalysisResult = data;
                
                // Persist state
                localStorage.setItem("last_analysis_result", JSON.stringify(data));

                // Reset AI assistant conversation since we have fresh context
                chatHistory = [
                    {
                        role: "assistant",
                        content: `Hello! I have reviewed ${payload.name || "the patient"}'s cardiometabolic screening results. The calculated risk score is ${data.risk_score}%, placing the patient in the ${data.risk_category} classification. The primary metabolic driver is ${data.simulator_projections.target_name}. How can I assist you with clinical interpretations or action plans?`
                    }
                ];
                localStorage.setItem("chat_history", JSON.stringify(chatHistory));
                renderChatHistory();

                // Populate tabs & enable navigation
                enableNavigationPills();
                renderInsightsPage(data);
                renderActionPlanPage(data);

                // Auto navigate to insights page
                navigateToTab("insights");
            }
        })
        .catch(err => {
            btnAnalyze.innerHTML = '<i class="fa-solid fa-heart-pulse"></i> Analyze Patient Risk';
            btnAnalyze.disabled = false;
            console.error(err);
            alert("Error running prediction engine. Please check your backend connection.");
        });
    });

    // -------------------------------------------------------------
    // Render Insights Page Data
    // -------------------------------------------------------------
    function renderInsightsPage(data) {
        if (!data) return;

        // 1. Risk summary banner classes and details
        riskSummaryBanner.className = "risk-banner"; // reset
        const cat = data.risk_category;
        const score = data.risk_score;
        const topDriver = data.simulator_projections.target_name;

        let categoryIcon = "fa-shield-halved";
        if (cat === "Low Risk") {
            riskSummaryBanner.classList.add("banner-green");
            bannerCategory.innerHTML = `<i class="fa-solid fa-circle-check"></i> Low Risk`;
            bannerPlan.textContent = "Recommended Plan: Routine Monitoring";
        } else if (cat === "Moderate Risk") {
            riskSummaryBanner.classList.add("banner-orange");
            bannerCategory.innerHTML = `<i class="fa-solid fa-circle-info"></i> Moderate Risk`;
            bannerPlan.textContent = "Recommended Plan: Lifestyle Intervention";
        } else {
            riskSummaryBanner.classList.add("banner-red");
            bannerCategory.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> High Risk`;
            bannerPlan.textContent = "Recommended Plan: Urgent Consultation";
        }

        bannerScore.textContent = `Score: ${score.toFixed(1)}%`;
        bannerDriver.textContent = `Primary Driver: ${topDriver}`;

        // 2. Executive summary content
        execSummaryContent.textContent = data.exec_summary;

        // 3. Render SHAP contribution chart bars
        shapChartContainer.innerHTML = "";
        if (data.risk_drivers && data.risk_drivers.length > 0) {
            data.risk_drivers.forEach(driver => {
                const row = document.createElement("div");
                row.className = "shap-row";

                let barColorClass = "bar-yellow";
                let emoji = "🟡";
                if (driver.contribution >= 15.0) {
                    barColorClass = "bar-red";
                    emoji = "🔴";
                } else if (driver.contribution >= 5.0) {
                    barColorClass = "bar-orange";
                    emoji = "🟠";
                }

                // Render dynamic bar width. Map the contribution to percentage of width.
                // Scale so 30% contribution fills 100% of the bar width
                const barWidth = Math.min(100, Math.max(8, (driver.contribution / 30) * 100));

                row.innerHTML = `
                    <span class="shap-label">${emoji} ${driver.label}</span>
                    <div class="shap-bar-bg">
                        <div class="shap-bar ${barColorClass}" style="width: ${barWidth}%;"></div>
                    </div>
                    <span class="shap-value">+${driver.contribution.toFixed(1)}%</span>
                `;
                shapChartContainer.appendChild(row);
            });
        } else {
            shapChartContainer.innerHTML = "<p class='card-description'>No significant metabolic risk attributions identified.</p>";
        }

        // 4. Render Recommended Actions (exactly 4 items)
        recommendedActionsList.innerHTML = "";
        if (data.recommended_actions) {
            data.recommended_actions.forEach(action => {
                const li = document.createElement("li");
                li.innerHTML = `<i class="fa-solid fa-circle-check action-checkmark"></i> ${action}`;
                recommendedActionsList.appendChild(li);
            });
        }

        // 5. Render clinical interpretations (up to 4 observations)
        clinicalInterpretationList.innerHTML = "";
        if (data.clinical_interpretation) {
            data.clinical_interpretation.forEach(obs => {
                const li = document.createElement("li");
                li.textContent = obs;
                clinicalInterpretationList.appendChild(li);
            });
        }
    }

    // -------------------------------------------------------------
    // Render Action Plan Page Data
    // -------------------------------------------------------------
    function renderActionPlanPage(data) {
        if (!data) return;

        // 1. Priority targets card
        const proj = data.simulator_projections;
        kpiTargetName.textContent = proj.target_name || "N/A";
        kpiCurrentVal.textContent = proj.current_val_str || "N/A";
        kpiTargetVal.textContent = proj.target_val_str || "N/A";
        kpiOutcome.textContent = proj.expected_outcome || "N/A";
        kpiTimeline.textContent = proj.estimated_timeline || "3–6 Months";

        interventionPriority.className = "priority-pill"; // reset
        if (proj.priority_label === "High") {
            interventionPriority.classList.add("pill-high");
            interventionPriority.textContent = "High Priority";
        } else if (proj.priority_label === "Medium") {
            interventionPriority.classList.add("pill-medium");
            interventionPriority.textContent = "Medium Priority";
        } else {
            interventionPriority.classList.add("pill-low");
            interventionPriority.textContent = "Low Priority";
        }

        // 2. Nutrition cards lists (exactly 3 bullet points)
        nutritionBulletsList.innerHTML = "";
        data.nutrition_bullets.forEach(bullet => {
            const li = document.createElement("li");
            li.textContent = bullet;
            nutritionBulletsList.appendChild(li);
        });

        // 3. Activity cards lists (exactly 3 bullet points)
        activityBulletsList.innerHTML = "";
        data.activity_bullets.forEach(bullet => {
            const li = document.createElement("li");
            li.textContent = bullet;
            activityBulletsList.appendChild(li);
        });

        // 4. Monitoring cards lists (exactly 3 bullet points)
        monitoringBulletsList.innerHTML = "";
        data.monitoring_bullets.forEach(bullet => {
            const li = document.createElement("li");
            li.textContent = bullet;
            monitoringBulletsList.appendChild(li);
        });
    }

    // -------------------------------------------------------------
    // AI Health Assistant Chats
    // -------------------------------------------------------------
    function formatMarkdown(text) {
        if (!text) return "";
        
        // Escape HTML characters to prevent XSS
        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
            
        // Bold: **text** -> <strong>text</strong>
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        
        // Bullet list items parsing
        const lines = escaped.split('\n');
        let inList = false;
        let formattedLines = [];
        
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            if (line.startsWith('* ') || line.startsWith('- ') || line.startsWith('• ')) {
                let content = line.substring(2).trim();
                // Italics: *text* -> <em>text</em>
                content = content.replace(/\*(.*?)\*/g, "<em>$1</em>");
                
                if (!inList) {
                    formattedLines.push('<ul style="margin: 6px 0; padding-left: 18px; list-style-type: disc;">');
                    inList = true;
                }
                formattedLines.push(`<li style="margin-bottom: 4px;">${content}</li>`);
            } else {
                if (inList) {
                    formattedLines.push('</ul>');
                    inList = false;
                }
                
                // Italics on normal lines: *text* -> <em>text</em>
                let inlineFormatted = line.replace(/\*(.*?)\*/g, "<em>$1</em>");
                formattedLines.push(inlineFormatted);
            }
        }
        
        if (inList) {
            formattedLines.push('</ul>');
        }
        
        // Build final HTML string
        let finalHtml = "";
        for (let i = 0; i < formattedLines.length; i++) {
            let cur = formattedLines[i];
            if (cur === '<ul style="margin: 6px 0; padding-left: 18px; list-style-type: disc;">' || cur === '</ul>' || cur.startsWith('<li')) {
                finalHtml += cur;
            } else {
                if (cur !== "") {
                    if (finalHtml !== "" && !finalHtml.endsWith('</ul>') && !finalHtml.endsWith('<ul style="margin: 6px 0; padding-left: 18px; list-style-type: disc;">')) {
                        finalHtml += "<br/>";
                    }
                    finalHtml += cur;
                } else {
                    finalHtml += "<br/>";
                }
            }
        }
        
        return finalHtml.replace(/(<br\/>)+/g, "<br/>").trim();
    }

    function renderChatHistory() {
        chatLogsArea.innerHTML = "";
        chatHistory.forEach(msg => {
            const bubble = document.createElement("div");
            bubble.classList.add("chat-bubble");
            if (msg.role === "assistant") {
                bubble.classList.add("bubble-assistant");
            } else {
                bubble.classList.add("bubble-user");
            }
            // Format markdown text to clean HTML
            bubble.innerHTML = formatMarkdown(msg.content);
            chatLogsArea.appendChild(bubble);
        });
        // Scroll to bottom
        chatLogsArea.scrollTop = chatLogsArea.scrollHeight;
    }

    function sendChatMessage(text) {
        if (!text || text.trim() === "") return;

        // Add user message
        chatHistory.push({ role: "user", content: text });
        renderChatHistory();
        chatInput.value = "";

        // Add typing indicator
        const typingBubble = document.createElement("div");
        typingBubble.className = "chat-bubble bubble-assistant typing-indicator";
        typingBubble.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Consulting AI risk models...';
        chatLogsArea.appendChild(typingBubble);
        chatLogsArea.scrollTop = chatLogsArea.scrollHeight;

        // Build context for chatbot
        const contextPayload = currentAnalysisResult ? {
            risk_score: currentAnalysisResult.risk_score,
            risk_category: currentAnalysisResult.risk_category,
            risk_drivers: currentAnalysisResult.risk_drivers,
            patient_dict: currentAnalysisResult.patient_dict,
            recommendations: currentAnalysisResult.recommendations,
            exec_summary: currentAnalysisResult.exec_summary,
            simulator_projections: currentAnalysisResult.simulator_projections
        } : {};

        fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages: chatHistory,
                patient_context: contextPayload
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Chat request failed");
            }
            return response.json();
        })
        .then(data => {
            // Remove typing bubble
            typingBubble.remove();

            // Add response
            chatHistory.push({ role: "assistant", content: data.response });
            localStorage.setItem("chat_history", JSON.stringify(chatHistory));
            renderChatHistory();
        })
        .catch(err => {
            typingBubble.remove();
            console.error(err);
            chatHistory.push({ 
                role: "assistant", 
                content: "I am having trouble accessing the clinical guidance models right now. Please verify your internet connection or try again." 
            });
            renderChatHistory();
        });
    }

    // Suggested questions pills click
    suggestedPillsContainer.addEventListener("click", (e) => {
        const btn = e.target.closest(".suggested-pill-btn");
        if (btn) {
            const query = btn.getAttribute("data-query");
            sendChatMessage(query);
        }
    });

    btnChatSend.addEventListener("click", () => {
        sendChatMessage(chatInput.value);
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendChatMessage(chatInput.value);
        }
    });

    // -------------------------------------------------------------
    // Export Assessment Report PDF
    // -------------------------------------------------------------
    btnExportPdf.addEventListener("click", () => {
        if (!currentAnalysisResult) {
            alert("No patient risk assessment available to export. Please analyze a patient first.");
            return;
        }

        btnExportPdf.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating report PDF...';
        btnExportPdf.disabled = true;

        const payload = {
            patient_dict: currentAnalysisResult.patient_dict,
            risk_score: currentAnalysisResult.risk_score,
            risk_category: currentAnalysisResult.risk_category,
            risk_drivers: currentAnalysisResult.risk_drivers,
            recommendations: currentAnalysisResult.recommendations,
            simulator_projections: currentAnalysisResult.simulator_projections,
            priority_areas: currentAnalysisResult.clinical_interpretation,
            exec_summary: currentAnalysisResult.exec_summary
        };

        fetch("/api/export", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Export PDF request failed");
            }
            return response.json();
        })
        .then(data => {
            btnExportPdf.innerHTML = '<i class="fa-solid fa-download"></i> Export Professional Screening Report';
            btnExportPdf.disabled = false;

            if (data.pdf_url) {
                // Trigger file download
                const link = document.createElement("a");
                link.href = data.pdf_url;
                link.download = data.pdf_url.split("/").pop();
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        })
        .catch(err => {
            btnExportPdf.innerHTML = '<i class="fa-solid fa-download"></i> Export Professional Screening Report';
            btnExportPdf.disabled = false;
            console.error(err);
            alert("Failed to export PDF clinical report.");
        });
    });

    // -------------------------------------------------------------
    // Boot Initialization
    // -------------------------------------------------------------
    init();
});
