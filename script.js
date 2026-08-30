// ============================================================
// CROPGUARD - MAIN JAVASCRIPT
// ============================================================


// ============================================================
// NAVIGATION
// ============================================================

function openDashboard() {
    window.location.href = "dashboard.html";
}


function scrollToFeatures() {

    const features = document.getElementById("features");

    if (features) {

        features.scrollIntoView({
            behavior: "smooth"
        });

    }

}


// ============================================================
// SAFE LOCAL STORAGE HELPERS
// ============================================================

function safeSetItem(key, value) {

    try {

        localStorage.setItem(key, value);

        return true;

    } catch (error) {

        console.warn(
            "⚠️ LocalStorage error:",
            error
        );

        return false;
    }

}


function safeGetJSON(key, fallback = []) {

    try {

        const value =
            localStorage.getItem(key);

        if (!value) {
            return fallback;
        }

        return JSON.parse(value);

    } catch (error) {

        console.warn(
            "⚠️ Could not read localStorage:",
            key
        );

        return fallback;
    }

}


// ============================================================
// COMPRESS IMAGE FOR LOCAL STORAGE
// ============================================================

function compressImage(file, maxWidth = 900, quality = 0.75) {

    return new Promise((resolve, reject) => {

        const reader =
            new FileReader();

        reader.onload = function (event) {

            const img =
                new Image();

            img.onload = function () {

                let width =
                    img.width;

                let height =
                    img.height;


                // --------------------------------------------
                // RESIZE LARGE IMAGES
                // --------------------------------------------

                if (width > maxWidth) {

                    const ratio =
                        maxWidth / width;

                    width =
                        maxWidth;

                    height =
                        Math.round(
                            height * ratio
                        );

                }


                const canvas =
                    document.createElement(
                        "canvas"
                    );


                canvas.width =
                    width;

                canvas.height =
                    height;


                const ctx =
                    canvas.getContext(
                        "2d"
                    );


                ctx.drawImage(
                    img,
                    0,
                    0,
                    width,
                    height
                );


                // --------------------------------------------
                // COMPRESS TO JPEG
                // --------------------------------------------

                const compressed =
                    canvas.toDataURL(
                        "image/jpeg",
                        quality
                    );


                resolve(
                    compressed
                );

            };


            img.onerror =
                function () {

                    reject(
                        new Error(
                            "Could not load image."
                        )
                    );

                };


            img.src =
                event.target.result;

        };


        reader.onerror =
            function () {

                reject(
                    new Error(
                        "Could not read image."
                    )
                );

            };


        reader.readAsDataURL(file);

    });

}


// ============================================================
// CROP IMAGE UPLOAD
// ============================================================

const imageInput =
    document.getElementById(
        "imageInput"
    );


if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            const file =
                this.files[0];


            if (!file) {
                return;
            }


            // --------------------------------------------
            // CHECK FILE TYPE
            // --------------------------------------------

            const allowedTypes = [

                "image/jpeg",

                "image/jpg",

                "image/png"

            ];


            if (
                !allowedTypes.includes(
                    file.type
                )
            ) {

                alert(
                    "Please choose a JPG, JPEG, or PNG image."
                );


                this.value = "";

                return;

            }


            // --------------------------------------------
            // SHOW PREVIEW
            // --------------------------------------------

            const reader =
                new FileReader();


            reader.onload =
                function (event) {

                    const previewImage =
                        document.getElementById(
                            "previewImage"
                        );


                    const previewBox =
                        document.getElementById(
                            "previewBox"
                        );


                    if (previewImage) {

                        previewImage.src =
                            event.target.result;

                    }


                    if (previewBox) {

                        previewBox.style.display =
                            "block";

                    }

                };


            reader.readAsDataURL(file);

        }
    );

}


// ============================================================
// ANALYZE CROP
// ============================================================

async function analyzeCrop() {

    const imageInput =
        document.getElementById(
            "imageInput"
        );


    // ========================================================
    // CHECK IMAGE
    // ========================================================

    if (
        !imageInput ||
        !imageInput.files.length
    ) {

        alert(
            "Please choose a crop image first."
        );

        return;

    }


    const file =
        imageInput.files[0];


    // ========================================================
    // CREATE FORM DATA
    // ========================================================

    const formData =
        new FormData();


    formData.append(
        "image",
        file
    );


    try {

        console.log(
            "🌱 Sending image to CropGuard backend..."
        );


        // ====================================================
        // SEND IMAGE TO FLASK
        // ====================================================

        const response =
            await fetch(
                "/analyze",
                {
                    method: "POST",
                    body: formData
                }
            );


        console.log(
            "Backend HTTP status:",
            response.status
        );


        // ====================================================
        // CHECK HTTP RESPONSE
        // ====================================================

        if (!response.ok) {

            throw new Error(
                "Backend returned HTTP " +
                response.status
            );

        }


        // ====================================================
        // READ JSON
        // ====================================================

        const data =
            await response.json();


        console.log(
            "🌱 AI RESULT:",
            data
        );


        // ====================================================
        // BACKEND SUCCESS
        // ====================================================

        if (data.success) {


            // =================================================
            // SAVE COMPRESSED IMAGE
            // =================================================

            console.log(
                "🖼️ Compressing image..."
            );


            let compressedImage = "";


            try {

                compressedImage =
                    await compressImage(
                        file,
                        900,
                        0.75
                    );


                console.log(
                    "✅ Image compressed successfully."
                );

            } catch (imageError) {

                console.warn(
                    "⚠️ Image compression failed:",
                    imageError
                );

            }


            // =================================================
            // SAVE CURRENT IMAGE
            // =================================================

            if (compressedImage) {

                const imageSaved =
                    safeSetItem(
                        "cropImage",
                        compressedImage
                    );


                if (!imageSaved) {

                    console.warn(
                        "⚠️ Could not save crop image."
                    );

                }

            }


            // =================================================
            // SAVE CURRENT AI RESULT
            // =================================================

            safeSetItem(
                "analysisResult",
                JSON.stringify(data)
            );


            // =================================================
            // GET EXISTING HISTORY
            // =================================================

            let scanHistory =
                safeGetJSON(
                    "scanHistory",
                    []
                );


            // Make sure history is actually an array

            if (!Array.isArray(scanHistory)) {

                scanHistory = [];

            }


            // =================================================
            // CREATE NEW SCAN
            // =================================================

            const newScan = {

                id:
                    Date.now(),


                crop:
                    data.crop ||
                    "Unable to identify",


                disease:
                    data.disease ||
                    "Uncertain result",


                confidence:
                    Number(
                        data.confidence || 0
                    ),


                severity:
                    data.severity ||
                    "Unknown",


                risk:
                    data.risk ||
                    "Unknown",


                status:
                    data.status ||
                    "uncertain",


                // IMPORTANT:
                // DO NOT STORE BASE64 IMAGE HERE
                image:
                    "",


                date:
                    new Date().toLocaleDateString(
                        "en-GB",
                        {
                            day: "2-digit",
                            month: "short",
                            year: "numeric"
                        }
                    ),


                cropIcon:
                    "🌱"

            };


            // =================================================
            // ADD NEW SCAN
            // =================================================

            scanHistory.push(
                newScan
            );


            // =================================================
            // KEEP ONLY LAST 20 SCANS
            // =================================================

            if (
                scanHistory.length >
                20
            ) {

                scanHistory =
                    scanHistory.slice(
                        -20
                    );

            }


            // =================================================
            // SAVE HISTORY
            // =================================================

            let historySaved =
                safeSetItem(
                    "scanHistory",
                    JSON.stringify(
                        scanHistory
                    )
                );


            // =================================================
            // IF STORAGE QUOTA ERROR
            // =================================================

            if (!historySaved) {

                console.warn(
                    "⚠️ Storage quota reached. Cleaning old scans..."
                );


                // Keep only latest 10

                scanHistory =
                    scanHistory.slice(
                        -10
                    );


                historySaved =
                    safeSetItem(
                        "scanHistory",
                        JSON.stringify(
                            scanHistory
                        )
                    );


                // If still failing, keep only current scan

                if (!historySaved) {

                    console.warn(
                        "⚠️ Still too large. Keeping only current scan."
                    );


                    historySaved =
                        safeSetItem(
                            "scanHistory",
                            JSON.stringify([
                                newScan
                            ])
                        );

                }

            }


            if (historySaved) {

                console.log(
                    "✅ Scan saved to history."
                );

            } else {

                console.warn(
                    "⚠️ Scan could not be saved to history."
                );

            }


            // =================================================
            // OPEN RESULT PAGE
            // =================================================

            window.location.href =
                "result.html";

        }


        // ====================================================
        // BACKEND RESPONSE BUT ANALYSIS FAILED
        // ====================================================

        else {

            alert(
                data.message ||
                "CropGuard could not analyze this image."
            );

        }


    } catch (error) {

        console.error(
            "❌ CropGuard error:",
            error
        );


        alert(
            "CropGuard error: " +
            error.message
        );

    }

}


// ============================================================
// SHOW IMAGE ON RESULT PAGE
// ============================================================

const resultImage =
    document.getElementById(
        "resultImage"
    );


if (resultImage) {

    const savedImage =
        localStorage.getItem(
            "cropImage"
        );


    if (savedImage) {

        resultImage.src =
            savedImage;

    }

}


// ============================================================
// RESULT PAGE - LOAD SAVED AI RESULT
// ============================================================

let analysisResult =
    null;


try {

    analysisResult =
        JSON.parse(
            localStorage.getItem(
                "analysisResult"
            )
        );

} catch (error) {

    console.warn(
        "⚠️ Could not load saved analysis."
    );

}


if (analysisResult) {

    console.log(
        "📊 Saved analysis:",
        analysisResult
    );

}


// ============================================================
// DASHBOARD LIVE DATA
// ============================================================

const totalCropsElement =
    document.getElementById(
        "totalCrops"
    );


if (totalCropsElement) {


    // ========================================================
    // GET HISTORY
    // ========================================================

    const history =
        safeGetJSON(
            "scanHistory",
            []
        );


    // ========================================================
    // BASIC COUNTS
    // ========================================================

    const totalScans =
        history.length;


    const uniqueCrops =
        new Set(

            history
                .map(
                    scan =>
                        scan.crop
                )
                .filter(
                    crop =>

                        crop &&

                        crop !==
                            "Unknown" &&

                        crop !==
                            "Unable to identify"

                )

        ).size;


    // ========================================================
    // HEALTHY SCANS
    // ========================================================

    const healthyScans =
        history.filter(
            scan => {

                const disease =
                    String(
                        scan.disease ||
                        ""
                    ).toLowerCase();


                const risk =
                    String(
                        scan.risk ||
                        ""
                    ).toLowerCase();


                const status =
                    String(
                        scan.status ||
                        ""
                    ).toLowerCase();


                return (

                    disease ===
                    "no disease detected"

                    ||

                    risk ===
                    "healthy"

                    ||

                    status ===
                    "healthy"

                );

            }
        ).length;


    // ========================================================
    // HIGH RISK
    // ========================================================

    const highRiskScans =
        history.filter(
            scan => {

                const risk =
                    String(
                        scan.risk ||
                        ""
                    ).toLowerCase();


                return (

                    risk ===
                    "high"

                    ||

                    risk ===
                    "high risk"

                );

            }
        ).length;


    // ========================================================
    // MODERATE RISK
    // ========================================================

    const moderateScans =
        history.filter(
            scan => {

                const risk =
                    String(
                        scan.risk ||
                        ""
                    ).toLowerCase();


                return (
                    risk ===
                    "moderate"
                );

            }
        ).length;


    // ========================================================
    // UPDATE STAT CARDS
    // ========================================================

    const totalCrops =
        document.getElementById(
            "totalCrops"
        );


    const totalScansElement =
        document.getElementById(
            "totalScans"
        );


    const highRiskElement =
        document.getElementById(
            "highRisk"
        );


    const healthyCountElement =
        document.getElementById(
            "healthyCount"
        );


    if (totalCrops) {

        totalCrops.textContent =
            uniqueCrops;

    }


    if (totalScansElement) {

        totalScansElement.textContent =
            totalScans;

    }


    if (highRiskElement) {

        highRiskElement.textContent =
            highRiskScans;

    }


    if (healthyCountElement) {

        healthyCountElement.textContent =
            healthyScans;

    }


    // ========================================================
    // RISK OVERVIEW
    // ========================================================

    const riskHealthy =
        document.getElementById(
            "riskHealthy"
        );


    const riskModerate =
        document.getElementById(
            "riskModerate"
        );


    const riskHigh =
        document.getElementById(
            "riskHigh"
        );


    if (riskHealthy) {

        riskHealthy.textContent =
            healthyScans;

    }


    if (riskModerate) {

        riskModerate.textContent =
            moderateScans;

    }


    if (riskHigh) {

        riskHigh.textContent =
            highRiskScans;

    }


    // ========================================================
    // HEALTHY PERCENTAGE
    // ========================================================

    let healthyPercentage =
        0;


    if (totalScans > 0) {

        healthyPercentage =
            Math.round(
                (
                    healthyScans /
                    totalScans
                ) * 100
            );

    }


    const healthyPercentageElement =
        document.getElementById(
            "healthyPercentage"
        );


    if (healthyPercentageElement) {

        healthyPercentageElement.textContent =
            healthyPercentage +
            "%";

    }


    // ========================================================
    // RECENT DIAGNOSES
    // ========================================================

    const recentContainer =
        document.getElementById(
            "recentDiagnoses"
        );


    if (recentContainer) {

        recentContainer.innerHTML =
            "";


        const recentScans =
            history
                .slice()
                .reverse()
                .slice(
                    0,
                    3
                );


        // ====================================================
        // NO SCANS
        // ====================================================

        if (
            recentScans.length ===
            0
        ) {

            recentContainer.innerHTML = `

                <p style="padding: 20px 0;">

                    No scans yet.
                    Start your first crop scan! 🌱

                </p>

            `;

        }


        // ====================================================
        // SHOW RECENT SCANS
        // ====================================================

        else {

            recentScans.forEach(
                scan => {


                    // ========================================
                    // CROP EMOJI
                    // ========================================

                    let cropEmoji =
                        "🌱";


                    const cropName =
                        String(
                            scan.crop ||
                            ""
                        ).toLowerCase();


                    if (

                        cropName.includes(
                            "corn"
                        )

                        ||

                        cropName.includes(
                            "maize"
                        )

                    ) {

                        cropEmoji =
                            "🌽";

                    }


                    else if (

                        cropName.includes(
                            "tomato"
                        )

                    ) {

                        cropEmoji =
                            "🍅";

                    }


                    else if (

                        cropName.includes(
                            "rice"
                        )

                    ) {

                        cropEmoji =
                            "🌾";

                    }


                    else if (

                        cropName.includes(
                            "potato"
                        )

                    ) {

                        cropEmoji =
                            "🥔";

                    }


                    else if (

                        cropName.includes(
                            "peach"
                        )

                    ) {

                        cropEmoji =
                            "🍑";

                    }


                    // ========================================
                    // STATUS
                    // ========================================

                    let statusClass =
                        "healthy-status";


                    let statusText =
                        "Healthy";


                    const risk =
                        String(
                            scan.risk ||
                            ""
                        ).toLowerCase();


                    const disease =
                        String(
                            scan.disease ||
                            ""
                        ).toLowerCase();


                    const status =
                        String(
                            scan.status ||
                            ""
                        ).toLowerCase();


                    // ----------------------------------------
                    // HEALTHY
                    // ----------------------------------------

                    if (

                        disease ===
                        "no disease detected"

                        ||

                        risk ===
                        "healthy"

                        ||

                        status ===
                        "healthy"

                    ) {

                        statusClass =
                            "healthy-status";

                        statusText =
                            "Healthy";

                    }


                    // ----------------------------------------
                    // HIGH RISK
                    // ----------------------------------------

                    else if (

                        risk ===
                        "high"

                        ||

                        risk ===
                        "high risk"

                    ) {

                        statusClass =
                            "high-status";

                        statusText =
                            "High Risk";

                    }


                    // ----------------------------------------
                    // MODERATE
                    // ----------------------------------------

                    else if (

                        risk ===
                        "moderate"

                    ) {

                        statusClass =
                            "moderate-status";

                        statusText =
                            "Moderate";

                    }


                    // ----------------------------------------
                    // UNKNOWN / UNCERTAIN
                    // ----------------------------------------

                    else {

                        statusClass =
                            "moderate-status";

                        statusText =
                            "Uncertain";

                    }


                    // ========================================
                    // CREATE ROW
                    // ========================================

                    const row =
                        document.createElement(
                            "div"
                        );


                    row.className =
                        "diagnosis-row";


                    row.innerHTML = `

                        <div class="crop-circle">

                            ${cropEmoji}

                        </div>


                        <div class="diagnosis-info">

                            <strong>

                                ${
                                    scan.crop ||
                                    "Unknown Crop"
                                }

                            </strong>


                            <span>

                                ${
                                    scan.disease ||
                                    "Unknown Condition"
                                }

                            </span>

                        </div>


                        <div class="
                            diagnosis-status
                            ${statusClass}
                        ">

                            ${statusText}

                        </div>

                    `;


                    recentContainer.appendChild(
                        row
                    );

                }
            );

        }

    }

}


// ============================================================
// DASHBOARD PAGE - LIVE DATA
// ============================================================

const dashboardPage =
    document.querySelector(
        ".dashboard-page"
    );


if (dashboardPage) {


    const history =
        safeGetJSON(
            "scanHistory",
            []
        );


    const totalScans =
        history.length;


    // ========================================================
    // HEALTHY
    // ========================================================

    const healthyScans =
        history.filter(
            item => {

                const disease =
                    String(
                        item.disease ||
                        ""
                    ).toLowerCase();


                const risk =
                    String(
                        item.risk ||
                        ""
                    ).toLowerCase();


                const status =
                    String(
                        item.status ||
                        ""
                    ).toLowerCase();


                return (

                    disease ===
                    "no disease detected"

                    ||

                    risk ===
                    "healthy"

                    ||

                    status ===
                    "healthy"

                );

            }
        ).length;


    // ========================================================
    // HIGH RISK
    // ========================================================

    const highRiskScans =
        history.filter(
            item => {

                const risk =
                    String(
                        item.risk ||
                        ""
                    ).toLowerCase();


                return (

                    risk ===
                    "high"

                    ||

                    risk ===
                    "high risk"

                );

            }
        ).length;


    // ========================================================
    // UNIQUE CROPS
    // ========================================================

    const uniqueCrops =
        new Set(

            history
                .map(
                    item =>
                        item.crop
                )
                .filter(
                    crop =>

                        crop &&

                        crop !==
                            "Unknown" &&

                        crop !==
                            "Unable to identify"

                )

        ).size;


    // ========================================================
    // UPDATE STAT CARDS
    // ========================================================

    const statCards =
        document.querySelectorAll(
            ".stat-card"
        );


    if (
        statCards.length >= 4
    ) {


        // -----------------------------------------------
        // TOTAL SCANS
        // -----------------------------------------------

        const card1 =
            statCards[0]
                .querySelector(
                    "h2"
                );


        if (card1) {

            card1.textContent =
                totalScans;

        }


        // -----------------------------------------------
        // UNIQUE CROPS
        // -----------------------------------------------

        const card2 =
            statCards[1]
                .querySelector(
                    "h2"
                );


        if (card2) {

            card2.textContent =
                uniqueCrops;

        }


        // -----------------------------------------------
        // HIGH RISK
        // -----------------------------------------------

        const card3 =
            statCards[2]
                .querySelector(
                    "h2"
                );


        if (card3) {

            card3.textContent =
                highRiskScans;

        }


        // -----------------------------------------------
        // HEALTHY
        // -----------------------------------------------

        const card4 =
            statCards[3]
                .querySelector(
                    "h2"
                );


        if (card4) {

            card4.textContent =
                healthyScans;

        }

    }

}


// ============================================================
// PAGE LOAD DEBUG
// ============================================================

console.log(
    "🌱 CropGuard script.js loaded successfully!"
);