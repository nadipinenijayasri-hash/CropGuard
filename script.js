function openDashboard() {
    window.location.href = "dashboard.html";
}

function scrollToFeatures() {
    document.getElementById("features").scrollIntoView({
        behavior: "smooth"
    });
}
// =========================
// CROP IMAGE UPLOAD
// =========================

const imageInput = document.getElementById("imageInput");

if (imageInput) {

    imageInput.addEventListener("change", function () {

        const file = this.files[0];

        if (file) {

            const reader = new FileReader();

            reader.onload = function (event) {

                document.getElementById("previewImage").src =
                    event.target.result;

                document.getElementById("previewBox").style.display =
                    "block";

            };

            reader.readAsDataURL(file);
        }

    });

}


// =========================
// ANALYZE CROP
// =========================

async function analyzeCrop() {

    const imageInput = document.getElementById("imageInput");

    if (!imageInput || !imageInput.files.length) {
        alert("Please choose a crop image first.");
        return;
    }

    const file = imageInput.files[0];

    const formData = new FormData();

    formData.append("image", file);


    try {

        const response = await fetch(
            "http://127.0.0.1:5000/analyze",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (data.success) {

    // Save the uploaded image
    const imageData =
        document.getElementById("previewImage").src;

    localStorage.setItem(
        "cropImage",
        imageData
    );


    // Save the current AI result
    localStorage.setItem(
        "analysisResult",
        JSON.stringify(data)
    );


    // =========================
    // SAVE SCAN TO HISTORY
    // =========================

    const scanHistory =
        JSON.parse(
            localStorage.getItem("scanHistory")
        ) || [];


    const newScan = {

        id: Date.now(),

        crop: data.crop,

        disease: data.disease,

        confidence: data.confidence,

        severity: data.severity,

        risk: data.risk,

        image: imageData,

        date: new Date().toLocaleDateString(
            "en-GB",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        ),

        cropIcon: "🌱"

    };


    // Add newest scan
    scanHistory.push(newScan);


    // Save updated history
    localStorage.setItem(
        "scanHistory",
        JSON.stringify(scanHistory)
    );


    // Go to result page
    window.location.href = "result.html";

}else {

            alert(data.message);

        }

    } catch (error) {

        console.error(error);

        alert(
            "Could not connect to CropGuard backend."
        );

    }
}
// =========================
// SHOW IMAGE ON RESULT PAGE
// =========================

const resultImage =
    document.getElementById("resultImage");

if (resultImage) {

    const savedImage =
        localStorage.getItem("cropImage");

    if (savedImage) {

        resultImage.src = savedImage;

    }

}
// =========================
// DASHBOARD LIVE DATA
// =========================

const totalCropsElement = document.getElementById("totalCrops");

if (totalCropsElement) {

    const history =
        JSON.parse(localStorage.getItem("scanHistory")) || [];

    // -------------------------
    // BASIC COUNTS
    // -------------------------

    const totalScans = history.length;

    const uniqueCrops = new Set(
        history.map(scan => scan.crop)
    ).size;

    const healthyScans = history.filter(scan =>
        scan.risk === "Healthy" ||
        scan.status === "Healthy" ||
        scan.disease === "No disease detected"
    ).length;

    const highRiskScans = history.filter(scan =>
        scan.risk === "High" ||
        scan.risk === "High Risk"
    ).length;

    const moderateScans = history.filter(scan =>
        scan.risk === "Moderate"
    ).length;


    // -------------------------
    // UPDATE STAT CARDS
    // -------------------------

    document.getElementById("totalCrops").textContent =
        uniqueCrops;

    document.getElementById("totalScans").textContent =
        totalScans;

    document.getElementById("highRisk").textContent =
        highRiskScans;

    document.getElementById("healthyCount").textContent =
        healthyScans;


    // -------------------------
    // RISK OVERVIEW
    // -------------------------

    document.getElementById("riskHealthy").textContent =
        healthyScans;

    document.getElementById("riskModerate").textContent =
        moderateScans;

    document.getElementById("riskHigh").textContent =
        highRiskScans;


    let healthyPercentage = 0;

    if (totalScans > 0) {
        healthyPercentage =
            Math.round((healthyScans / totalScans) * 100);
    }

    document.getElementById("healthyPercentage").textContent =
        healthyPercentage + "%";


    // -------------------------
    // RECENT DIAGNOSES
    // -------------------------

    const recentContainer =
        document.getElementById("recentDiagnoses");

    if (recentContainer) {

        recentContainer.innerHTML = "";

        const recentScans =
            history.slice().reverse().slice(0, 3);

        if (recentScans.length === 0) {

            recentContainer.innerHTML = `
                <p style="padding: 20px 0;">
                    No scans yet. Start your first crop scan! 🌱
                </p>
            `;

        } else {

            recentScans.forEach(scan => {

                let cropEmoji = "🌱";

                if (
                    scan.crop &&
                    scan.crop.toLowerCase().includes("corn")
                ) {
                    cropEmoji = "🌽";
                }
                else if (
                    scan.crop &&
                    scan.crop.toLowerCase().includes("maize")
                ) {
                    cropEmoji = "🌽";
                }
                else if (
                    scan.crop &&
                    scan.crop.toLowerCase().includes("tomato")
                ) {
                    cropEmoji = "🍅";
                }
                else if (
                    scan.crop &&
                    scan.crop.toLowerCase().includes("rice")
                ) {
                    cropEmoji = "🌾";
                }


                let statusClass = "healthy-status";
                let statusText = "Healthy";

                if (
                    scan.risk === "High" ||
                    scan.risk === "High Risk"
                ) {
                    statusClass = "high-status";
                    statusText = "High Risk";
                }
                else if (scan.risk === "Moderate") {
                    statusClass = "moderate-status";
                    statusText = "Moderate";
                }


                const row = document.createElement("div");

                row.className = "diagnosis-row";

                row.innerHTML = `

                    <div class="crop-circle">
                        ${cropEmoji}
                    </div>

                    <div class="diagnosis-info">

                        <strong>
                            ${scan.crop || "Unknown Crop"}
                        </strong>

                        <span>
                            ${scan.disease || "Unknown Condition"}
                        </span>

                    </div>

                    <div class="diagnosis-status ${statusClass}">
                        ${statusText}
                    </div>

                `;

                recentContainer.appendChild(row);

            });

        }

    }

}
// =========================
// LIVE DASHBOARD DATA
// =========================

const dashboardPage = document.querySelector(".dashboard-page");

if (dashboardPage) {

    const history =
        JSON.parse(localStorage.getItem("scanHistory")) || [];

    const totalScans = history.length;

    const healthyScans =
        history.filter(item =>
            String(item.risk).toLowerCase().includes("healthy")
        ).length;
    const highRiskScans =
        history.filter(item =>
            String(item.risk).toLowerCase().includes("high")
        ).length;
    // Update stat cards
    const statCards =
        document.querySelectorAll(".stat-card");

    if (statCards.length >= 4) {

        statCards[0].querySelector("h2").textContent =
            totalScans;

        statCards[1].querySelector("h2").textContent =
            totalScans;

        statCards[2].querySelector("h2").textContent =
            highRiskScans;

        statCards[3].querySelector("h2").textContent =
            healthyScans;
    }

}
// =========================
// CLEAR OLD TEST HISTORY
// =========================

localStorage.removeItem("scanHistory");