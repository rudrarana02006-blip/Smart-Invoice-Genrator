# 🚀 Devleds Engine
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
   git clone https://github.com/rudrarana02006-blip/Smart-Invoice-Generator.git
   cd Smart-Invoice-Generator
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   MONGODB_URI=your_mongodb_uri
   GEMINI_API_KEY=your_google_ai_key
   ADMIN_EMAIL=your_admin_email
   ```

4. **Run the Server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

---

*Built with ❤️ by Devleds.*
