# 🚀 Devleds Engine

```text
 __________________________________________          .----------------------------------.
/  ______________________________________  \         |  DE V L E D S                    |
|  /                                      \  |        |  ==============================  |
|  |   █▀▀▄ █▀▀ █  █ █    █▀▀ █▀▀▄ █▀▀      |  |        |  INV-2026-001                    |
|  |   █  █ █▀▀ ▀▄▄▀ █    █▀▀ █  █ ▀▀█      |  |        |  Date: 2026-05-17                |
|  |   ▀▀▀  ▀▀▀  ▀▀  ▀▀▀  ▀▀▀ ▀▀▀  ▀▀▀      |  |        |  ------------------------------  |
|  |                                        |  |        |  ITEMS             QTY     RATE  |
|  |   [ INTELLIGENT BILLING SYSTEM ]       |  |        |  - AI Branding      1      FREE  |
|  |   ------------------------------       |  |        |  - Liquid Glass     1      FREE  |
|  |   STATUS : ACTIVE                      |  |        |  - Dev Engine       1      FREE  |
|  |   SYSTEM : LIQUID GLASS v2.0           |  |        |  ------------------------------  |
|  |   ENGINE : GEMINI HYBRID               |  |        |  TOTAL                     $0.00  |
|  |                                        |  |        |  ==============================  |
|  |         .-------------------.          |  |        |  THANK YOU!                      |
|  |        /  AI STYLE CLONING  \          |  |        '----------------------------------'
|  |       |   [████████████] 100%|         |  |
|  |        \___________________/          |  |
|  \________________________________________/  |
 \____________________________________________/
```

> **The future of intelligent billing. Powered by AI. Defined by Design.**

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Gemini%20AI-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)

---

## ✨ Overview
Devleds Engine is a high-performance, design-centric billing platform. It goes beyond simple document generation by utilizing **AI Vision** to clone design aesthetics from any sample invoice, allowing for "Style DNA" extraction and automated professional branding.

## 🌟 Key Features
- **🧠 AI Style Cloning**: Upload a JPEG/PDF of any invoice. Our Gemini-powered engine analyzes the "Design DNA" (typography, spacing, color palettes) and replicates it for your business.
- **🧊 Liquid Glass UI**: A premium dashboard experience with glassmorphism, organic animations, and a focus on specular edge aesthetics.
- **📊 Real-time Analytics**: Built-in financial intelligence with geographical billing heatmaps and revenue velocity tracking.
- **📜 Multi-Engine PDF Export**: High-fidelity PDF generation using professional-grade rendering engines.
- **🔐 Enterprise Security**: Full JWT authentication, organization-level management, and automated email security verification.

---

## 📘 User Manual & Feature Guide

Welcome to the **Devleds Engine** user manual. Below is a detailed, feature-by-feature guide to navigating and getting the most out of the system.

### 1. 🔐 Authentication & Onboarding
*   **Registration & Setup**: When you first sign up, you'll create an administrator profile for your organization.
*   **Organization Profile**: Under settings, configure your company details (Legal Name, Complete Postal Address, Logo, Tax Registration Status). This data is automatically mapped to all outgoing invoices.
*   **Secure OTP Password Reset**: If you ever forget your password, click the *Forgot Password* link. The system instantly generates a secure, single-use 6-digit OTP code and emails it to your registered inbox to securely authenticate password changes without third-party redirects.

### 2. 🧊 Liquid Glass Dashboard
*   **Real-time KPIs**: Instantly monitor your organization's performance with active tracking blocks for:
    *   *Total Invoiced Amount* (Cumulative earnings)
    *   *Unpaid Invoices* (Outstanding receivables)
    *   *Active Clients* (Active corporate partnerships)
*   **Revenue Velocity Charts**: An interactive canvas showing monthly billing trends, enabling you to track financial growth visually.
*   **Geographical Heatmaps**: A high-end visualization showing billing density across cities and states, helping you locate your main markets.

### 3. 👥 Client Management
*   **Direct Client Directory**: Keep a dedicated list of business clients. Store crucial business details including corporate email addresses, telephone numbers, and billing addresses.
*   **Quick Association**: When generating an invoice, simply select a pre-saved client from the dropdown list to automatically populate all invoice billing fields.

### 4. ✍️ Real-Time Invoice Creator
*   **Interactive Row Additions**: Add unlimited line items to your invoice with detailed description, quantity, and individual unit rate parameters.
*   **Instant Computations**: Subtotal, applicable tax margins, individual item values, and grand total balances are computed automatically in real-time as you type, completely eliminating manual math errors.
*   **Flexible Due Dates**: Assign custom due dates for clear payment timeline enforcement.

### 5. 🧠 AI Style Cloning (The Flagship Feature)
*   **Clone Any Design**: Found a beautifully formatted invoice online or have a physical corporate design you wish to replicate? Simply navigate to the *AI Style Cloning* portal.
*   **Intelligent Analysis**: Drag & drop or upload any image (JPEG, PNG) or PDF copy of the design.
*   **Extract Style DNA**: Powered by **Google Gemini AI**, the system automatically processes the visual document, extracts its precise style guidelines (colour palette codes, font typography styling, padding/margins, table borders, and alignment styles), and instantly saves them to your organization's custom active layout format.
*   **Apply Universally**: Once cloned, all future generated invoices will automatically utilize the extracted style layout!

### 6. 📜 High-Fidelity PDF Exporting
*   **Pixel-Perfect Conversions**: Print or download your invoices dynamically. The WeasyPrint/Jinja2 PDF rendering hybrid engine converts active style layouts and invoice data into high-fidelity, printable PDF documents in seconds.

---

## 🛠️ Architecture & Tech Stack
- **Backend**: FastAPI (Asynchronous Python)
- **Database**: MongoDB Atlas (NoSQL)
- **AI Core**: Google Gemini 1.5 Pro / 2.0 Flash
- **PDF Engine**: WeasyPrint / Jinja2 Hybrid
- **Frontend**: Premium Vanilla JS / CSS (Liquid Glass System)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MongoDB Atlas Account
- Google Gemini API Key

### Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/devleds-prod/smart-invoice-generator.git
   cd smart-invoice-generator
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Copy the `.env.example` template to `.env`:
   ```bash
   cp .env.example .env
   ```
   Open the newly created `.env` file and fill in your custom credentials:
   - **MONGODB_URI**: Your MongoDB database connection string.
   - **GEMINI_API_KEY**: Your API key from Google AI Studio.
   - **MAIL_USERNAME & MAIL_PASSWORD**: Your SMTP email address and 16-character App Password (if using Gmail) to enable the system to send automated OTPs to your users.

4. **Run the Server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

---

*Built with ❤️ by Devleds.*
