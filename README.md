# sicss-profile-digger

## **🚀 Quick Start: Run This Scraper on Your Machine**

### **1. 📦 Clone the project**

```
git clone https://github.com/yourname/sicss-profile-digger.git
cd sicss-profile-digger
```

---

### **2. 🐍 Install PDM and dependencies**

> PDM is a modern Python package manager (like Poetry or Pipenv).


```
pip install pdm  # Install PDM globally (if not already)
pdm install       # Install all project dependencies
pdm run playwright install  # Install browser drivers for Playwright
```

---

### **3. 🚀 Run the scraper**

```
pdm run scrape
```

This will start scraping profiles and save them to the **data/raw/** folder.

---

### **4. 📁 Output**

* **CSV file(s): **data/raw/profiles_xxx.csv
* (Optional) Photos: **data/raw/images/xxx/** (if enabled)

---

### **🛠️ Troubleshooting**

* Make sure you’re using **Python 3.9+**
* **If **playwright** is not found, run: **pdm install && pdm run playwright install
* If errors persist, try **pdm info** to confirm you’re in the correct virtual environment

---

### **✅ Requirements (auto-installed)**

* Python ≥ 3.9
* [pdm](https://pdm.fming.dev/)
* playwright**, **requests**, **beautifulsoup4
