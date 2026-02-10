#include <WiFi.h>
#include <WebServer.h>
#include <EEPROM.h>

// إعدادات الواي فاي
const char* ssid = "TEKMER WIFI";
const char* password = "IAU-Tekmer2025";

// Static IP Configuration
IPAddress localIP(10, 155, 83, 100);      // IP ثابت
IPAddress gateway(10, 155, 83, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);

// LED Configuration
#define LED_BLUE 2        // LED الأزرق (GPIO 2)
#define GSR_PIN 34        // منفذ ADC لقراءة GSR
#define LED_BLINK_INTERVAL 500  // مللي ثانية
const float R_SERIES = 10000.0; // قيمة المقاومة المتسلسلة (R1) في دائرة مقسم الجهد (10k Ohm)
const float ADC_MAX = 4095.0;   // أقصى قيمة لـ ADC في ESP32 (12-bit)

WebServer server(80);

// متغيرات LED
bool wifiConnected = false;
unsigned long lastLEDToggle = 0;
bool ledState = LOW;

// تعريف مراحل التجربة
struct Stage {
  const char* name;
  unsigned long duration; // المدة بالمللي ثانية
  const char* description;
};

Stage stages[] = {
  {"callibration", 20000, "callibration (20 seconds)"},
  {"Normal stage", 240000, "Normal stage (4 minutes)"},
  {"Stress", 180000, "Stress (3 minutes)"},
  {"Relaxation", 60000, "Relaxation (1 minute)"},
  {"Session complete", 0, "Session complete"}
};

bool recording = false;
unsigned long sessionStartTime = 0;
unsigned long stageStartTime = 0;
int currentStage = 0;

// دالة قراءة مستشعر GSR وتحويلها إلى مقاومة (R_gsr)
float readGSRResistance() {
  int gsrRaw = analogRead(GSR_PIN);
  float resistance = 0.0;
  
  if (gsrRaw > 0) { 
    resistance = (R_SERIES * (ADC_MAX / gsrRaw)) - R_SERIES;
  } else {
    resistance = 999999999.0;
  }
  
  return resistance;
}

// دالة تحديث المرحلة وإعداد استجابة JSON
String getStageJson() {
  if (!recording) {
    // إذا كانت الجلسة متوقفة، نرسل مؤشر للمرحلة النهائية إذا كان هو الحالي
    if (currentStage == sizeof(stages)/sizeof(Stage) - 1) {
        return "{\"finished\": true}"; 
    }
    return "{}";
  }

  unsigned long now = millis();
  unsigned long elapsed = now - sessionStartTime;
  unsigned long totalDuration = 0;
  
  int oldStage = currentStage;
  for (int i = 0; i < sizeof(stages)/sizeof(Stage) - 1; i++) {
    totalDuration += stages[i].duration;
    if (elapsed < totalDuration) {
      if (i != currentStage) {
        currentStage = i;
        stageStartTime = now;
      }
      break;
    }
  }

  // التعامل مع المرحلة النهائية
  if (elapsed >= totalDuration) {
    currentStage = sizeof(stages)/sizeof(Stage) - 1;
    recording = false;
    // إذا انتهت الجلسة، نرسل مؤشر "finished: true"
    return "{\"finished\": true}";
  }

  // قراءة المقاومة بالمعادلة الجديدة
  float resistance = readGSRResistance(); 

  // حساب المؤقتات
  unsigned long stageElapsed = now - stageStartTime;
  unsigned long stageDuration = stages[currentStage].duration;
  unsigned long stageRemaining = stageDuration > stageElapsed ? 
                                stageDuration - stageElapsed : 0;

  // بناء JSON
  String json = "{";
  json += "\"elapsed\":" + String(elapsed / 1000) + ",";
  json += "\"remaining\":" + String(stageRemaining / 1000) + ",";
  json += "\"value\":" + String(resistance, 2) + ",";
  json += "\"stage\":\"" + String(stages[currentStage].name) + "\",";
  json += "\"description\":\"" + String(stages[currentStage].description) + "\",";
  json += "\"stageDuration\":" + String(stageDuration / 1000);
  json += "}";

  return json;
}

// الهيكل الكامل لصفحة الويب
const char htmlPage[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GSR Stress Monitor - Mohammed Saleh</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <style>
    /* Page styles with camera box support */
    :root {
      --primary: #3b82f6; /* أزرق */
      --secondary: #10b981; /* أخضر */
      --surface: #f3f4f6; /* فاتح */
      --background: #ffffff;
      --text: #1f2937;
      --subtext: #6b7280;
    }
    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--background);
      color: var(--text);
      margin: 0;
      padding: 20px;
      display: flex;
      justify-content: center;
      min-height: 100vh;
    }
    .container {
      width: 100%;
      max-width: 1200px;
    }
    header {
      text-align: center;
      margin-bottom: 30px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--surface);
    }
    header h1 {
      color: var(--primary);
      margin: 0;
      font-weight: 600;
    }
    .controls {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-bottom: 30px;
    }
    .button {
      padding: 10px 20px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: background-color 0.3s;
      font-weight: 500;
    }
    #startButton {
      background-color: var(--secondary);
      color: white;
    }
    #startButton:hover:not(:disabled) { background-color: #059669; }
    #stopButton {
      background-color: #ef4444; /* أحمر */
      color: white;
    }
    #stopButton:hover:not(:disabled) { background-color: #dc2626; }
    .button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .card {
      background-color: var(--surface);
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
      text-align: center;
    }
    .card-title {
      font-size: 14px;
      color: var(--subtext);
      margin-bottom: 5px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .card-value {
      font-size: 32px;
      font-weight: 600;
      color: var(--text);
    }
    .chart-container {
      background-color: var(--surface);
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
      height: 400px;
      position: relative;
    }
    .stage-info {
      margin-bottom: 30px;
      padding: 15px;
      border: 1px solid var(--primary);
      border-radius: 8px;
      background-color: #eff6ff;
    }
    .stage-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .stage-header h2 {
      margin: 0;
      font-size: 20px;
      color: var(--primary);
    }
    .stage-timer-display {
      font-size: 24px;
      font-weight: 600;
      color: #ef4444;
    }
    .progress-bar-container {
      background-color: #e5e7eb;
      border-radius: 4px;
      height: 8px;
      overflow: hidden;
      margin-top: 10px;
    }
    #stageProgress {
      height: 100%;
      width: 0%;
      background-color: var(--primary);
      transition: width 1s linear;
    }

    /* Camera box (top-left) */
    .cam-box{ position:fixed; top:20px; left:20px; width:220px; height:160px; background:#ffffffcc; border-radius:10px; overflow:hidden; box-shadow:0 6px 18px rgba(0,0,0,0.12); z-index:1200; display:flex; align-items:center; justify-content:center; flex-direction:column }
    .cam-box video{ width:100%; height:100%; object-fit:cover }
    .cam-overlay{ position:absolute; left:6px; top:6px; right:6px; display:flex; justify-content:space-between; align-items:center; gap:6px }
    #camStatus{ font-size:12px; color:#0f172a; background:#ffffffcc; padding:4px 8px; border-radius:6px }
    #enableCamBtn{ padding:6px 8px; font-size:12px; border-radius:6px; border:none; background:#3b82f6; color:#fff; cursor:pointer }
  </style>
</head>
<body>
  <div class="container">
      <div id="camBox" class="cam-box" aria-live="polite">
        <video id="localVideo" autoplay playsinline muted></video>
        <div id="camOverlay" class="cam-overlay">
          <div id="camStatus">Camera: inactive — click Enable</div>
          <button id="enableCamBtn">Enable Camera</button>
        </div>
      </div>
      <header>
        <h1>GSR Stress Monitor</h1>
        <p>Real-time Galvanic Skin Response (GSR) Monitoring</p>
        <p id="connectionStatus" style="font-size: 14px; color: #10b981;"><i class="fas fa-check-circle"></i> ESP32 Connected: 10.155.83.100</p>
      </header>

    <div class="controls">
      <input type="number" id="volunteerIdInput" placeholder="Volunteer ID" min="1" style="padding: 10px 20px; border: 1px solid var(--subtext); border-radius: 8px; font-size: 16px;">
      <button id="startButton" class="button">
        <i class="fas fa-play"></i> Start Session
      </button>
      <button id="stopButton" class="button" disabled>
        <i class="fas fa-stop"></i> Stop & Download CSV
      </button>
    </div>

    <div class="stage-info">
      <div class="stage-header">
        <h2>Stage: <span id="stageDescription">Waiting to start...</span></h2>
        <div class="stage-timer-display">
          <i class="fas fa-clock"></i> Remaining: <span id="stageTimer">--:--</span>
        </div>
      </div>
      <div class="progress-bar-container">
        <div id="stageProgress"></div>
      </div>
    </div>

    <div class="stats-grid">
      <div class="card">
        <div class="card-title">Resistance Value</div>
        <div class="card-value" id="resistanceValue">0.00 Ω</div>
      </div>
      <div class="card">
        <div class="card-title">Session Elapsed Time</div>
        <div class="card-value" id="sessionTimer">00:00</div>
      </div>
    </div>

    <div class="chart-container">
      <canvas id="chart"></canvas>
    </div>

    <script>
      // تكوين الـ IP الثابت للـ ESP32
      const ESP32_IP = "10.155.83.100";
      const ESP32_PORT = 80;
      const ESP32_URL = `http://${ESP32_IP}:${ESP32_PORT}`;
      
      // التحقق من الاتصال بالـ ESP32 عند تحميل الصفحة
      window.addEventListener('load', () => {
        checkESP32Connection();
      });
      
      async function checkESP32Connection() {
        try {
          const response = await fetch(`${ESP32_URL}/resistance`, {
            method: 'GET',
            mode: 'no-cors'
          });
          document.getElementById('connectionStatus').innerHTML = 
            '<i class="fas fa-check-circle"></i> ESP32 Connected: ' + ESP32_IP;
          document.getElementById('connectionStatus').style.color = '#10b981';
        } catch (err) {
          document.getElementById('connectionStatus').innerHTML = 
            '<i class="fas fa-exclamation-circle"></i> ESP32 Not Connected - Check IP';
          document.getElementById('connectionStatus').style.color = '#ef4444';
          console.warn('ESP32 not reachable at', ESP32_URL);
        }
      }

      // Initialize chart.js safely: if CDN failed to load, don't stop the rest of the script
      let chart = null;
      try {
        const ctxEl = document.getElementById('chart');
        if (ctxEl && typeof Chart !== 'undefined') {
          const ctx = ctxEl.getContext('2d');
          chart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: [],
              datasets: [{
                label: 'Resistance (Ω)',
                data: [],
                borderColor: getComputedStyle(document.documentElement).getPropertyValue('--primary') || '#3b82f6',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 0,
                fill: false,
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  mode: 'index',
                  intersect: false,
                  backgroundColor: 'var(--surface)',
                  titleColor: '#94A3B8',
                  bodyColor: 'var(--text)'
                }
              },
              scales: {
                x: { 
                  title: { 
                    display: true, 
                    text: 'Time (seconds)', 
                    color: 'var(--text)' 
                  },
                  ticks: { color: 'var(--subtext)' },
                  grid: { color: '#e5e7eb' }
                },
                y: { 
                  title: { 
                    display: true, 
                    text: 'Resistance (Ω)', 
                    color: 'var(--text)' 
                  },
                  ticks: { color: 'var(--subtext)' },
                  grid: { color: '#e5e7eb' }
                }
              }
            }
          });
        } else {
          console.warn('Chart.js not loaded or canvas missing. Chart disabled.');
        }
      } catch (err) {
        console.error('Chart initialization failed:', err);
      }

      let dataLog = [];
      let sessionActive = false;
      let intervalId = null;
      // متغير لتتبع ما إذا كان التحميل التلقائي قد حدث بالفعل
      let autoDownloadExecuted = false;
      // متغير لحفظ ملف الفيديو
      let mediaRecorder = null;
      let recordedChunks = [];
      let videoStream = null; 

      // دالة موحدة لتحميل ملف CSV
      function downloadCSV() {
        // إذا كان dataLog فارغاً أو التحميل التلقائي قد حدث، نخرج
        if (dataLog.length === 0) {
            console.log("No data to download.");
            return;
        }

        const csv = dataLog.reduce((acc, row) => 
          acc += `${row.elapsed},${row.value},${row.stage}\n`, 
          "Time (s),Resistance (Ω),Stage\n"
        );
        
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "GSR_Data.csv";
        a.click();
        URL.revokeObjectURL(url);
        console.log("CSV file successfully generated and downloaded!");
        
        // محاولة رفع الملف إلى OneDrive
        uploadToOneDrive(blob, "GSR_Data.csv");
      }
      
      // دالة رفع ملف إلى OneDrive
      async function uploadToOneDrive(blob, filename) {
        const volunteerId = document.getElementById("volunteerIdInput").value;
        
        if (!volunteerId) {
          console.warn("Volunteer ID not provided. Skipping OneDrive upload.");
          return;
        }
        
        try {
          // تحويل البيانات إلى Base64 للرفع
          const reader = new FileReader();
          reader.onload = async () => {
            const base64Data = reader.result.split(',')[1];
            
            // إرسال طلب الرفع إلى الخادم الخلفي
            const uploadResponse = await fetch('http://localhost:5000/api/upload', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                volunteer_id: volunteerId,
                filename: filename,
                file_data: base64Data,
                email: 'kfupm@almutlaqunited.com',
                password: 'Muc@2026'  // تحذير: يجب تخزينها بشكل آمن!
              })
            });
            
            if (uploadResponse.ok) {
              console.log('File uploaded to OneDrive successfully');
            } else {
              console.warn('Failed to upload to OneDrive:', uploadResponse.statusText);
            }
          };
          reader.readAsDataURL(blob);
          
        } catch (error) {
          console.error('Error uploading to OneDrive:', error);
        }
      }

      document.getElementById("startButton").onclick = () => {
        dataLog = [];
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.update();
        autoDownloadExecuted = false; // إعادة تعيين حالة التحميل التلقائي
        
        fetch(`${ESP32_URL}/start`)
          .then(() => {
            document.getElementById("startButton").disabled = true;
            document.getElementById("stopButton").disabled = false; // الزر شغال
            sessionActive = true;
            if (!intervalId) {
              intervalId = setInterval(fetchData, 1000);
            }
          })
          .catch(error => console.error('Error starting session:', error));
      };

      document.getElementById("stopButton").onclick = () => {
        fetch(`${ESP32_URL}/stop`)
          .then(() => {
            document.getElementById("startButton").disabled = false;
            document.getElementById("stopButton").disabled = true; // يتم تعطيله بعد الضغط اليدوي
            sessionActive = false;
            
            if (intervalId) {
              clearInterval(intervalId);
              intervalId = null;
            }
            downloadCSV(); // تحميل الملف عند الضغط اليدوي
          })
          .catch(error => console.error('Error stopping session:', error));
      };

      function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      }

      async function fetchData() {
        if(!sessionActive) {
            // التحقق من التحميل التلقائي في حالة توقف الجلسة
            if (!autoDownloadExecuted && dataLog.length > 0) {
                document.getElementById("stageDescription").textContent = "Session complete. Downloading data...";
                downloadCSV();
                autoDownloadExecuted = true;
                // بعد التحميل التلقائي، يمكننا إيقاف المؤقت
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
            }
            return;
        }
        
        try {
          const response = await fetch(`${ESP32_URL}/resistance`);
          const data = await response.json();
          
          if (Object.keys(data).length === 0 || data.finished) {
            // الجلسة انتهت تلقائياً (finished: true أو {})
            
            document.getElementById("startButton").disabled = false;
            document.getElementById("stopButton").disabled = false; // **** أهم تعديل: الزر يبقى مفعلاً
            sessionActive = false;
            
            document.getElementById("stageDescription").textContent = "Session complete. Ready for download (Auto-downloading...)";
            
            if (!autoDownloadExecuted) {
                downloadCSV(); // التحميل التلقائي عند الانتهاء
                autoDownloadExecuted = true;
            }
            
            if (intervalId) {
              clearInterval(intervalId);
              intervalId = null;
            }
            
            return;
          }

          // تحديث عناصر الواجهة
          document.getElementById("stageTimer").textContent = formatTime(data.remaining);
          document.getElementById("stageDescription").textContent = data.description;
          document.getElementById("sessionTimer").textContent = formatTime(data.elapsed);
          
          let resistanceDisplay = data.value > 100000000 ? (data.value / 1000000).toFixed(2) + " MΩ" : data.value.toFixed(2) + " Ω";
          document.getElementById("resistanceValue").textContent = resistanceDisplay;
          
          const progress = (1 - (data.remaining / data.stageDuration)) * 100;
          document.getElementById("stageProgress").style.width = `${progress}%`;

          // تحديث الرسم البياني
          if (chart.data.labels.length >= 600) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
          }
          chart.data.labels.push(data.elapsed);
          chart.data.datasets[0].data.push(data.value);
          chart.update();

          // تسجيل البيانات
          dataLog.push({
            elapsed: data.elapsed,
            value: data.value,
            stage: data.stage
          });

        } catch(error) {
          console.error('Error fetching data:', error);
        }
      }

        // Camera handling: request camera permission and start local video on page load
        const videoEl = document.getElementById('localVideo');
        const camStatus = document.getElementById('camStatus');
        const enableBtn = document.getElementById('enableCamBtn');

        function isSafari(){ return /^((?!chrome|android).)*safari/i.test(navigator.userAgent); }

        async function startCamera(){
          if(!navigator || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
            camStatus.textContent = 'Camera API not supported';
            enableBtn.style.display = 'none';
            console.warn('getUserMedia not available');
            return;
          }
          try{
            camStatus.textContent = 'Camera: requesting...';
            const stream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user' }, audio:false });
            videoEl.srcObject = stream;
            camStatus.textContent = 'Camera: active';
            enableBtn.style.display = 'none';
            console.log('Camera stream started');
          } catch(err){
            console.error('Camera start failed:', err);
            if(isSafari()){
              camStatus.textContent = 'Camera blocked by Safari (requires HTTPS). Try Chrome or enable manually.';
            } else {
              camStatus.textContent = 'Camera blocked/unavailable — click Enable to retry';
            }
            enableBtn.style.display = 'inline-block';
          }
        }

        enableBtn.onclick = () => { startCamera(); };

        window.addEventListener('load', () => {
          if(!navigator || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
            camStatus.textContent = 'Camera API not supported';
            enableBtn.style.display = 'none';
          } else {
            enableBtn.style.display = 'inline-block';
            if(isSafari()){
              camStatus.textContent = 'Safari may require HTTPS; click Enable or use Chrome';
            } else {
              camStatus.textContent = 'Requesting camera access...';
              // try to start camera immediately (may be blocked on some browsers)
              startCamera();
            }
          }
        });
    </script>
</body>
</html>
)rawliteral";

void setup() {
  Serial.begin(115200);
  pinMode(GSR_PIN, INPUT);
  pinMode(LED_BLUE, OUTPUT);
  digitalWrite(LED_BLUE, LOW);  // إطفاء LED في البداية

  analogReadResolution(12); // تعيين دقة القراءة إلى 12 بت (4096 قيمة)

  // تكوين الـ Static IP قبل الاتصال
  if (!WiFi.config(localIP, gateway, subnet, primaryDNS)) {
    Serial.println("Failed to configure Static IP");
  }

  // الاتصال بالواي فاي
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi with Static IP");
  
  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 20) {
    delay(500);
    Serial.print(".");
    wifiAttempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nFailed to connect to WiFi");
    wifiConnected = false;
  }

  // تحديد مسارات الخادم (Server Routes)
  server.on("/", HTTP_GET, []() {
    server.send_P(200, "text/html", htmlPage);
  });

  server.on("/start", HTTP_GET, []() {
    recording = true;
    sessionStartTime = millis();
    stageStartTime = millis();
    currentStage = 0;
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Session started");
  });

  server.on("/stop", HTTP_GET, []() {
    recording = false;
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Session stopped");
  });

  server.on("/resistance", HTTP_GET, []() {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", getStageJson());
  });

  // Explicit favicon handler to stop browser favicon requests causing "request handler not found"
  server.on("/favicon.ico", HTTP_GET, []() {
    server.send(204, "image/x-icon", "");
  });

  // Fallback handler to catch requests with no explicit handler (avoids WebServer.cpp: _handleRequest errors)
  server.onNotFound([](){
    String uri = server.uri();
    Serial.print("NotFound: "); Serial.println(uri);
    if (uri == "/favicon.ico") {
      // respond with no content for favicon requests
      server.send(204, "image/x-icon", "");
      return;
    }
    // generic 404 for other missing resources
    server.send(404, "text/plain", "Not found");
  });

  server.begin();
}

void loop() {
  server.handleClient();
  
  // LED Blinking Logic - يومض عند الاتصال، يتوقف عند قطع الاتصال
  unsigned long currentTime = millis();
  bool currentWiFiStatus = (WiFi.status() == WL_CONNECTED);
  
  // تحديث حالة الاتصال
  if (currentWiFiStatus != wifiConnected) {
    wifiConnected = currentWiFiStatus;
    if (wifiConnected) {
      Serial.println("WiFi Connected! IP: " + WiFi.localIP().toString());
    } else {
      Serial.println("WiFi Disconnected!");
      digitalWrite(LED_BLUE, LOW);  // إطفاء LED عند فقدان الاتصال
    }
  }
  
  // التحكم في LED: يومض إذا كان متصل
  if (wifiConnected && (currentTime - lastLEDToggle >= LED_BLINK_INTERVAL)) {
    ledState = !ledState;
    digitalWrite(LED_BLUE, ledState);
    lastLEDToggle = currentTime;
  }
}