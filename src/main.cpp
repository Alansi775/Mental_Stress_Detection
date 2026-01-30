#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>

// إعدادات الواي فاي
const char* ssid = "HUAWEI-100A7N";
const char* password = "Trabzon6167";

WebServer server(80);

#define GSR_PIN 34 // منفذ ADC لقراءة GSR
const float R_SERIES = 10000.0; // قيمة المقاومة المتسلسلة (R1) في دائرة مقسم الجهد (10k Ohm)
const float ADC_MAX = 4095.0;   // أقصى قيمة لـ ADC في ESP32 (12-bit)

#define LED_PIN 2
bool wifiConnected = false;
unsigned long lastBlinkTime = 0;
bool ledState = false;
const unsigned long BLINK_INTERVAL = 1000; // blink when not connected
const int WIFI_ATTEMPTS = 60; // number of 500ms attempts = 30s
Preferences prefs;

// تعريف مراحل التجربة
struct Stage {
  const char* name;
  unsigned long duration; // المدة بالمللي ثانية
  const char* description;
};

Stage stages[] = {
  {"Calibration", 20000, "System calibration (20 seconds)"},
  {"Normal", 240000, "Watch video (4 minutes)"},
  {"Stress", 180000, "Remove 12 pieces with 85dB noise (3 minutes)"},
  {"Relaxation", 60000, "Relax with music (1 minute)"},
  {"Finished", 0, "Session complete"}
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
    // إذا كانت الجلسة متوقفة، نرسل JSON غير فارغ حتى لا تعتبر الواجهة أن الجلسة انتهت
    if (currentStage == sizeof(stages)/sizeof(Stage) - 1) {
        return "{\"finished\": true}"; 
    }
    String j = "{";
    j += "\"elapsed\":0,";
    j += "\"remaining\":" + String(stages[0].duration / 1000) + ",";
    j += "\"value\":0.00,";
    j += "\"stage\":\"Idle\",";
    j += "\"description\":\"Idle\",";
    j += "\"stageDuration\":0";
    j += "}";
    return j;
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
    /* ... (Your CSS styles remain unchanged) ... */
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
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>GSR Stress Monitor</h1>
      <p>Real-time Galvanic Skin Response (GSR) Monitoring</p>
    </header>

    <div class="controls">
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
      const ctx = document.getElementById('chart').getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Resistance (Ω)',
            data: [],
            borderColor: 'var(--primary)',
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

      let dataLog = [];
      let sessionActive = false;
      let intervalId = null;
      // متغير لتتبع ما إذا كان التحميل التلقائي قد حدث بالفعل
      let autoDownloadExecuted = false; 

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
      }

      document.getElementById("startButton").onclick = () => {
        dataLog = [];
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.update();
        autoDownloadExecuted = false; // إعادة تعيين حالة التحميل التلقائي
        
        fetch("/start")
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
        fetch("/stop")
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
          const response = await fetch('/resistance');
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
    </script>
</body>
</html>
)rawliteral";

// AP fallback credentials
const char* ap_ssid = "GSR_Monitor";
const char* ap_pass = "12341234";

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(GSR_PIN, INPUT);

  analogReadResolution(12); // تعيين دقة القراءة إلى 12 بت (4096 قيمة)
  // Force AP-only mode per user request (do not attempt STA)
  Serial.println("Starting Access Point (AP-only) per user request");
  WiFi.mode(WIFI_AP);
  bool ok = WiFi.softAP(ap_ssid, ap_pass);
  if (!ok) {
    Serial.println("Failed to start AP with password; starting open AP");
    WiFi.softAP(ap_ssid);
  } else {
    Serial.print("AP password: ");
    Serial.println(ap_pass);
  }
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
  wifiConnected = true; // treat AP as connected for UI
  digitalWrite(LED_PIN, HIGH);
  ledState = true;

  // تحديد مسارات الخادم (Server Routes)
  server.on("/", HTTP_GET, []() {
    Serial.println("HTTP / (root) called");
    server.send_P(200, "text/html", htmlPage);
  });

  // respond to common icon requests with empty 204 to avoid connection resets
  server.on("/favicon.ico", HTTP_GET, []() {
    Serial.println("HTTP /favicon.ico called");
    server.send(204, "image/x-icon", "");
  });
  server.on("/apple-touch-icon.png", HTTP_GET, []() {
    Serial.println("HTTP /apple-touch-icon.png called");
    server.send(204, "image/png", "");
  });
  server.on("/apple-touch-icon-precomposed.png", HTTP_GET, []() {
    Serial.println("HTTP /apple-touch-icon-precomposed.png called");
    server.send(204, "image/png", "");
  });

  // simple ping endpoint for diagnostics
  server.on("/ping", HTTP_GET, []() {
    Serial.println("HTTP /ping called");
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "ok");
  });

  server.onNotFound([](){
    Serial.printf("HTTP NOT FOUND: %s\n", server.uri().c_str());
    server.send(404, "text/plain", "Not found");
  });

  server.on("/start", HTTP_GET, []() {
    Serial.println("HTTP /start called");
    recording = true;
    sessionStartTime = millis();
    stageStartTime = millis();
    currentStage = 0;
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Session started");
  });

  server.on("/stop", HTTP_GET, []() {
    Serial.println("HTTP /stop called");
    recording = false;
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Session stopped");
  });

  server.on("/resistance", HTTP_GET, []() {
    Serial.println("HTTP /resistance called");
    server.sendHeader("Access-Control-Allow-Origin", "*");
    String j = getStageJson();
    server.send(200, "application/json", j);
  });

  // API to scan nearby networks (returns JSON array)
  server.on("/scan", HTTP_GET, []() {
    int n = WiFi.scanNetworks();
    String j = "[";
    for (int i = 0; i < n; ++i) {
      if (i) j += ",";
      j += "{\"ssid\":\"" + WiFi.SSID(i) + "\",\"rssi\":" + String(WiFi.RSSI(i)) + "}";
    }
    j += "]";
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", j);
  });

  // Save WiFi credentials (GET params: ssid, pass) - convenience endpoint
  server.on("/save", HTTP_GET, []() {
    String s = server.arg("ssid");
    String p = server.arg("pass");
    Serial.printf("Save request SSID='%s' PASS='%s'\n", s.c_str(), p.c_str());
    if (s.length() == 0) {
      server.send(400, "text/plain", "missing ssid");
      return;
    }
    prefs.begin("credentials", false);
    prefs.putString("ssid", s);
    prefs.putString("pass", p);
    prefs.end();

    // attempt connect immediately
    WiFi.mode(WIFI_STA);
    WiFi.begin(s.c_str(), p.c_str());
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < WIFI_ATTEMPTS) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nConnected to saved network: " + WiFi.localIP().toString());
      server.send(200, "text/plain", "ok");
    } else {
      Serial.println("\nFailed to connect to saved network");
      server.send(500, "text/plain", "failed");
    }
  });

  server.begin();
  Serial.println("Server Started!");
}

void loop() {
  server.handleClient();

  unsigned long now = millis();
  unsigned long interval = recording ? 200 : BLINK_INTERVAL;
  if (now - lastBlinkTime >= interval) {
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    lastBlinkTime = now;
  }
}