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

    const features =
        document.getElementById("features");

    if (features) {

        features.scrollIntoView({
            behavior: "smooth"
        });

    }
}


// ============================================================
// LOCAL STORAGE HELPERS
// ============================================================

function safeSetItem(key, value) {

    try {

        localStorage.setItem(
            key,
            value
        );

        return true;

    } catch (error) {

        console.warn(
            "LocalStorage error:",
            error
        );

        return false;
    }
}


function safeGetJSON(
    key,
    fallback = []
) {

    try {

        const value =
            localStorage.getItem(key);

        if (!value) {
            return fallback;
        }

        return JSON.parse(value);

    } catch (error) {

        console.warn(
            "Could not read localStorage:",
            key
        );

        return fallback;
    }
}


// ============================================================
// INDEXED DB
//
// IMPORTANT:
// Images are stored separately.
// Each scan has its OWN image.
// ============================================================

const DB_NAME =
    "CropGuardDB";

const DB_VERSION =
    2;

const IMAGE_STORE =
    "scanImages";

let dbPromise = null;


// ============================================================
// OPEN DATABASE
// ============================================================

function openDatabase() {

    if (dbPromise) {
        return dbPromise;
    }


    dbPromise =
        new Promise(
            function(resolve, reject) {

                if (!window.indexedDB) {

                    reject(
                        new Error(
                            "IndexedDB is not supported."
                        )
                    );

                    return;
                }


                const request =
                    indexedDB.open(
                        DB_NAME,
                        DB_VERSION
                    );


                request.onupgradeneeded =
                    function(event) {

                        const db =
                            event.target.result;


                        if (
                            !db.objectStoreNames.contains(
                                IMAGE_STORE
                            )
                        ) {

                            db.createObjectStore(
                                IMAGE_STORE,
                                {
                                    keyPath: "id"
                                }
                            );

                        }

                    };


                request.onsuccess =
                    function() {

                        const db =
                            request.result;


                        db.onclose =
                            function() {
                                dbPromise = null;
                            };


                        resolve(db);

                    };


                request.onerror =
                    function() {

                        dbPromise = null;

                        reject(
                            request.error
                        );

                    };

            }
        );


    return dbPromise;
}


// ============================================================
// SAVE IMAGE
// ============================================================

async function saveScanImage(
    scanId,
    imageData
) {

    const db =
        await openDatabase();


    return new Promise(
        function(resolve, reject) {

            const transaction =
                db.transaction(
                    IMAGE_STORE,
                    "readwrite"
                );


            const store =
                transaction.objectStore(
                    IMAGE_STORE
                );


            store.put({

                id: String(scanId),

                image: imageData

            });


            transaction.oncomplete =
                function() {

                    resolve(true);

                };


            transaction.onerror =
                function() {

                    reject(
                        transaction.error
                    );

                };

        }
    );
}


// ============================================================
// GET IMAGE
// ============================================================

async function getScanImage(
    scanId
) {

    try {

        const db =
            await openDatabase();


        return new Promise(
            function(resolve, reject) {

                const transaction =
                    db.transaction(
                        IMAGE_STORE,
                        "readonly"
                    );


                const store =
                    transaction.objectStore(
                        IMAGE_STORE
                    );


                const request =
                    store.get(
                        String(scanId)
                    );


                request.onsuccess =
                    function() {

                        if (
                            request.result
                        ) {

                            resolve(
                                request.result.image
                            );

                        } else {

                            resolve(null);

                        }

                    };


                request.onerror =
                    function() {

                        reject(
                            request.error
                        );

                    };

            }
        );

    } catch (error) {

        console.error(
            "Could not get scan image:",
            error
        );

        return null;
    }
}


// ============================================================
// DELETE IMAGE
// ============================================================

async function deleteScanImage(
    scanId
) {

    try {

        const db =
            await openDatabase();


        return new Promise(
            function(resolve, reject) {

                const transaction =
                    db.transaction(
                        IMAGE_STORE,
                        "readwrite"
                    );


                const store =
                    transaction.objectStore(
                        IMAGE_STORE
                    );


                store.delete(
                    String(scanId)
                );


                transaction.oncomplete =
                    function() {

                        resolve(true);

                    };


                transaction.onerror =
                    function() {

                        reject(
                            transaction.error
                        );

                    };

            }
        );

    } catch (error) {

        console.warn(
            "Could not delete image:",
            error
        );

        return false;
    }
}


// ============================================================
// IMAGE COMPRESSION
// ============================================================

function compressImage(
    file,
    maxWidth = 900,
    quality = 0.75
) {

    return new Promise(
        function(resolve, reject) {

            const reader =
                new FileReader();


            reader.onload =
                function(event) {

                    const img =
                        new Image();


                    img.onload =
                        function() {

                            let width =
                                img.width;

                            let height =
                                img.height;


                            if (
                                width > maxWidth
                            ) {

                                const ratio =
                                    maxWidth /
                                    width;


                                width =
                                    maxWidth;


                                height =
                                    Math.round(
                                        height *
                                        ratio
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
                        function() {

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
                function() {

                    reject(
                        new Error(
                            "Could not read image."
                        )
                    );

                };


            reader.readAsDataURL(
                file
            );

        }
    );
}


// ============================================================
// MIGRATE OLD HISTORY
//
// Old scans may have:
// image: "data:image/..."
//
// New scans use:
// imageKey: "unique-id"
// ============================================================

async function migrateOldHistory() {

    let history =
        safeGetJSON(
            "scanHistory",
            []
        );


    if (
        !Array.isArray(history)
    ) {
        return;
    }


    let changed =
        false;


    for (
        const scan of history
    ) {

        if (!scan) {
            continue;
        }


        // Already has image key
        if (scan.imageKey) {
            continue;
        }


        // Old image exists
        if (
            scan.image &&
            typeof scan.image === "string" &&
            scan.image.startsWith("data:image")
        ) {

            try {

                const id =
                    scan.id ||
                    (
                        Date.now() +
                        "-" +
                        Math.random()
                            .toString(36)
                            .substring(2, 9)
                    );


                scan.id =
                    id;


                await saveScanImage(
                    id,
                    scan.image
                );


                scan.imageKey =
                    String(id);


                delete scan.image;


                changed =
                    true;


                console.log(
                    "Migrated old scan image:",
                    id
                );

            } catch (error) {

                console.warn(
                    "Could not migrate old image:",
                    error
                );

            }

        }

    }


    if (changed) {

        try {

            localStorage.setItem(
                "scanHistory",
                JSON.stringify(history)
            );

            console.log(
                "Old scan history migrated successfully."
            );

        } catch (error) {

            console.warn(
                "Could not save migrated history:",
                error
            );

        }

    }

}


// Run migration
migrateOldHistory()
    .catch(
        function(error) {

            console.warn(
                "History migration failed:",
                error
            );

        }
    );


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
        function() {

            const file =
                this.files[0];


            if (!file) {
                return;
            }


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


                this.value =
                    "";


                return;
            }


            const reader =
                new FileReader();


            reader.onload =
                function(event) {

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


            reader.readAsDataURL(
                file
            );

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


    const formData =
        new FormData();


    formData.append(
        "image",
        file
    );


    try {

        console.log(
            "Sending image to CropGuard backend..."
        );


        // ====================================================
        // SEND TO FLASK
        // ====================================================

        const response =
            await fetch(
                "/analyze",
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!response.ok) {

            throw new Error(
                "Backend returned HTTP " +
                response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "AI RESULT:",
            data
        );


        if (!data.success) {

            alert(
                data.message ||
                "CropGuard could not analyze this image."
            );

            return;
        }


        // ====================================================
        // CREATE UNIQUE SCAN ID
        // ====================================================

        const scanId =
            Date.now() +
            "-" +
            Math.random()
                .toString(36)
                .substring(2, 9);


        // ====================================================
        // COMPRESS IMAGE
        // ====================================================

        console.log(
            "Compressing image..."
        );


        let compressedImage;


        try {

            compressedImage =
                await compressImage(
                    file,
                    900,
                    0.75
                );

        } catch (error) {

            console.error(
                "Image compression failed:",
                error
            );


            alert(
                "Could not process the uploaded image."
            );


            return;
        }


        // ====================================================
        // SAVE IMAGE TO INDEXED DB
        //
        // IMPORTANT:
        // NO IMAGE IS SAVED TO LOCAL STORAGE.
        // ====================================================

        await saveScanImage(
            scanId,
            compressedImage
        );


        console.log(
            "Image saved in IndexedDB:",
            scanId
        );


        // ====================================================
        // SAVE CURRENT RESULT
        // ====================================================

        safeSetItem(
            "analysisResult",
            JSON.stringify(data)
        );


        // ====================================================
        // REMEMBER WHICH SCAN IS CURRENT
        //
        // Only the ID is stored.
        // ====================================================

        safeSetItem(
            "selectedScanId",
            String(scanId)
        );


        // ====================================================
        // GET HISTORY
        // ====================================================

        let scanHistory =
            safeGetJSON(
                "scanHistory",
                []
            );


        if (
            !Array.isArray(scanHistory)
        ) {

            scanHistory =
                [];

        }


        // ====================================================
        // CREATE NEW SCAN
        // ====================================================

        const newScan = {

            id:
                String(scanId),

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

            // ONLY THE IMAGE KEY
            imageKey:
                String(scanId),

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
                getCropIcon(
                    data.crop
                )

        };


        // ====================================================
        // ADD NEW SCAN
        // ====================================================

        scanHistory.push(
            newScan
        );


        // ====================================================
        // KEEP LAST 20
        // ====================================================

        if (
            scanHistory.length > 20
        ) {

            const removedScans =
                scanHistory.splice(
                    0,
                    scanHistory.length - 20
                );


            for (
                const oldScan
                of removedScans
            ) {

                if (
                    oldScan &&
                    oldScan.imageKey
                ) {

                    await deleteScanImage(
                        oldScan.imageKey
                    );

                }

            }

        }


        // ====================================================
        // SAVE HISTORY
        // ====================================================

        const historySaved =
            safeSetItem(
                "scanHistory",
                JSON.stringify(
                    scanHistory
                )
            );


        if (!historySaved) {

            alert(
                "Scan completed, but history could not be saved."
            );

            return;
        }


        console.log(
            "Scan saved successfully:",
            scanId
        );


        // ====================================================
        // OPEN RESULT PAGE
        // ====================================================

        window.location.href =
            "result.html";


    } catch (error) {

        console.error(
            "CropGuard error:",
            error
        );


        alert(
            "CropGuard error: " +
            error.message
        );

    }

}


// ============================================================
// CROP ICON
// ============================================================

function getCropIcon(crop) {

    const name =
        String(
            crop || ""
        ).toLowerCase();


    if (
        name.includes("corn") ||
        name.includes("maize")
    ) {

        return "🌽";

    }


    if (
        name.includes("tomato")
    ) {

        return "🍅";

    }


    if (
        name.includes("rice")
    ) {

        return "🌾";

    }


    if (
        name.includes("potato")
    ) {

        return "🥔";

    }


    if (
        name.includes("peach")
    ) {

        return "🍑";

    }


    if (
        name.includes("apple")
    ) {

        return "🍎";

    }


    if (
        name.includes("grape")
    ) {

        return "🍇";

    }


    if (
        name.includes("strawberry")
    ) {

        return "🍓";

    }


    return "🌱";
}


// ============================================================
// RESULT PAGE
//
// IMPORTANT:
// Result image is loaded from IndexedDB.
// NOT localStorage.
// ============================================================

async function loadResultPage() {

    const resultImage =
        document.getElementById(
            "cropImage"
        );


    if (!resultImage) {
        return;
    }


    // ========================================================
    // GET CURRENT SCAN ID
    // ========================================================

    const selectedScanId =
        localStorage.getItem(
            "selectedScanId"
        );


    // ========================================================
    // LOAD IMAGE FROM INDEXED DB
    // ========================================================

    if (selectedScanId) {

        try {

            const image =
                await getScanImage(
                    selectedScanId
                );


            if (image) {

                resultImage.src =
                    image;


                console.log(
                    "Correct scan image loaded:",
                    selectedScanId
                );

            } else {

                console.warn(
                    "No image found for scan:",
                    selectedScanId
                );

                resultImage.removeAttribute(
                    "src"
                );

            }

        } catch (error) {

            console.error(
                "Could not load result image:",
                error
            );

        }

    }


    // ========================================================
    // LOAD RESULT
    // ========================================================

    let result =
        null;


    try {

        const saved =
            localStorage.getItem(
                "analysisResult"
            );


        if (saved) {

            result =
                JSON.parse(
                    saved
                );

        }

    } catch (error) {

        console.warn(
            "Could not load analysis result."
        );

    }


    if (!result) {
        return;
    }


    const cropName =
        document.getElementById(
            "cropName"
        );


    const diseaseName =
        document.getElementById(
            "diseaseName"
        );


    const confidenceText =
        document.getElementById(
            "confidenceText"
        );


    const confidenceBar =
        document.getElementById(
            "confidenceBar"
        );


    const severity =
        document.getElementById(
            "severity"
        );


    const risk =
        document.getElementById(
            "risk"
        );


    // ========================================================
    // UNCERTAIN
    // ========================================================

    if (
        result.status ===
        "uncertain"
    ) {

        if (cropName) {

            cropName.textContent =
                result.crop ||
                "Unable to identify";

        }


        if (diseaseName) {

            diseaseName.textContent =
                result.disease ||
                "Uncertain result";

        }


        if (confidenceText) {

            confidenceText.textContent =
                result.confidence ||
                0;

        }


        if (confidenceBar) {

            confidenceBar.style.width =
                (
                    result.confidence ||
                    0
                ) + "%";

        }


        if (severity) {

            severity.textContent =
                "Unknown";

        }


        if (risk) {

            risk.textContent =
                "Unknown";

        }


        return;
    }


    // ========================================================
    // SUCCESS
    // ========================================================

    if (
        result.status ===
        "success"
    ) {

        if (cropName) {

            cropName.textContent =
                result.crop ||
                "Unknown";

        }


        if (diseaseName) {

            diseaseName.textContent =
                result.disease ||
                "Unknown";

        }


        if (confidenceText) {

            confidenceText.textContent =
                result.confidence ||
                0;

        }


        if (confidenceBar) {

            confidenceBar.style.width =
                (
                    result.confidence ||
                    0
                ) + "%";

        }


        if (severity) {

            severity.textContent =
                result.severity ||
                "Unknown";

        }


        if (risk) {

            risk.textContent =
                result.risk ||
                "Unknown";

        }

    }

}


// ============================================================
// RUN RESULT PAGE
// ============================================================

loadResultPage();


// ============================================================
// DASHBOARD DATA
// ============================================================

function updateDashboard() {

    const totalCropsElement =
        document.getElementById(
            "totalCrops"
        );


    if (!totalCropsElement) {
        return;
    }


    const history =
        safeGetJSON(
            "scanHistory",
            []
        );


    if (!Array.isArray(history)) {
        return;
    }


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
                        "Unable to identify"
                )

        ).size;


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


    const highRiskScans =
        history.filter(
            scan => {

                const risk =
                    String(
                        scan.risk ||
                        ""
                    ).toLowerCase();


                return (

                    risk === "high" ||

                    risk === "high risk"

                );

            }
        ).length;


    const moderateScans =
        history.filter(
            scan => {

                const risk =
                    String(
                        scan.risk ||
                        ""
                    ).toLowerCase();


                return (

                    risk === "moderate" ||

                    risk === "medium"

                );

            }
        ).length;


    // ========================================================
    // STAT CARDS
    // ========================================================

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


    if (totalCropsElement) {

        totalCropsElement.textContent =
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

    const healthyPercentageElement =
        document.getElementById(
            "healthyPercentage"
        );


    let healthyPercentage =
        0;


    if (totalScans > 0) {

        healthyPercentage =
            Math.round(
                (
                    healthyScans /
                    totalScans
                ) *
                100
            );

    }


    if (
        healthyPercentageElement
    ) {

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


    if (!recentContainer) {
        return;
    }


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


    if (
        recentScans.length === 0
    ) {

        recentContainer.innerHTML = `

            <p style="padding:20px 0;">
                No scans yet.
                Start your first crop scan! 🌱
            </p>

        `;

        return;
    }


    recentScans.forEach(
        scan => {

            const cropEmoji =
                getCropIcon(
                    scan.crop
                );


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

            else if (

                risk === "high" ||

                risk === "high risk"

            ) {

                statusClass =
                    "high-status";

                statusText =
                    "High Risk";

            }

            else if (

                risk === "moderate" ||

                risk === "medium"

            ) {

                statusClass =
                    "moderate-status";

                statusText =
                    "Moderate";

            }

            else {

                statusClass =
                    "moderate-status";

                statusText =
                    "Uncertain";

            }


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


// ============================================================
// UPDATE DASHBOARD
// ============================================================

updateDashboard();


// ============================================================
// DASHBOARD PAGE STAT CARDS
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
        Array.isArray(history)
            ? history.length
            : 0;


    const healthyScans =
        Array.isArray(history)
            ? history.filter(
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


                    return (

                        disease ===
                        "no disease detected"

                        ||

                        risk ===
                        "healthy"

                    );

                }
            ).length
            : 0;


    const highRiskScans =
        Array.isArray(history)
            ? history.filter(
                scan => {

                    const risk =
                        String(
                            scan.risk ||
                            ""
                        ).toLowerCase();


                    return (

                        risk === "high" ||

                        risk === "high risk"

                    );

                }
            ).length
            : 0;


    const uniqueCrops =
        new Set(

            Array.isArray(history)

                ? history

                    .map(
                        scan =>
                            scan.crop
                    )

                    .filter(
                        crop =>
                            crop &&
                            crop !==
                            "Unable to identify"
                    )

                : []

        ).size;


    const statCards =
        document.querySelectorAll(
            ".stat-card"
        );


    if (
        statCards.length >= 4
    ) {

        const card1 =
            statCards[0]
                .querySelector("h2");


        const card2 =
            statCards[1]
                .querySelector("h2");


        const card3 =
            statCards[2]
                .querySelector("h2");


        const card4 =
            statCards[3]
                .querySelector("h2");


        if (card1) {
            card1.textContent =
                totalScans;
        }


        if (card2) {
            card2.textContent =
                uniqueCrops;
        }


        if (card3) {
            card3.textContent =
                highRiskScans;
        }


        if (card4) {
            card4.textContent =
                healthyScans;
        }

    }

}


// ============================================================
// DEBUG
// ============================================================

console.log(
    "🌱 CropGuard script.js loaded successfully!"
);

console.log(
    "🖼️ Images are stored separately per scan in IndexedDB."
);