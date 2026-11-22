\# 🔐 CipherChain

\### AI-Powered Secure Messaging with Blockchain Integration



CipherChain is a secure messaging application that combines Artificial Intelligence, cryptographic techniques, and Blockchain technology to provide secure communication, detect suspicious messages, and verify message integrity.



\## 🚀 Key Features



\- \*\*Secure Messaging:\*\* AES-256-GCM encryption for message protection.

\- \*\*Secure Key Exchange:\*\* ECDH P-256 and HKDF-SHA256.

\- \*\*AI Threat Detection:\*\* Machine learning-based detection of SAFE, PHISHING, and SPAM messages.

\- \*\*Blockchain Integration:\*\* Records encrypted message payload hashes on the blockchain.

\- \*\*Message Integrity Verification:\*\* Detects unauthorized modifications by comparing message hashes.

\- \*\*Analytics Dashboard:\*\* Displays messaging and security information.



\## 🛠️ Technology Stack



| Component | Technology |

|---|---|

| Frontend | React |

| Backend | Python, FastAPI |

| Database | SQLite |

| Machine Learning | Scikit-learn, TF-IDF, Logistic Regression |

| Blockchain | Solidity, Hardhat, Web3.py |

| Cryptography | AES-256-GCM, ECDH, HKDF, SHA-256 |



\## 🧠 AI Model



The machine learning model classifies messages into three categories:



\- SAFE

\- PHISHING

\- SPAM



The model uses TF-IDF feature extraction and Logistic Regression.



\*\*Test accuracy:\*\* 97.33% on the held-out test dataset.



\## ⛓️ Blockchain Integration



CipherChain uses a Solidity smart contract named `MessageIntegrity`.



It stores encrypted message payload hashes along with blockchain timestamps and recorder addresses. The application can verify whether a stored message payload matches its recorded hash.



The current Hardhat configuration uses a local development blockchain.



\## 🔒 Security Features



\- Encrypted message payloads

\- Cryptographic key exchange

\- Message authentication using AES-GCM

\- SHA-256 integrity hashing

\- Blockchain-based integrity verification

\- AI-based suspicious message detection



\## 📂 Project Structure



```text

CipherChain/

├── backend/

│   ├── ai/

│   ├── api/

│   └── main.py

├── frontend/

├── smart-contracts/

│   ├── contracts/

│   ├── scripts/

│   └── deployments/

├── datasets/

├── trained\_models\_real/

├── trained\_models/

├── requirements.txt

└── README.md

```



\## ⚙️ Installation and Setup



\### 1. Clone the repository



```bash

git clone https://github.com/RakeshBG195/CipherChain.git

cd CipherChain

```



\### 2. Set up the Python backend



```bash

python -m venv .venv

```



Activate the virtual environment on Windows:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



Install dependencies:



```bash

pip install -r requirements.txt

```



Start the backend:



```bash

python -m uvicorn backend.main:app --reload

```



Backend: `http://127.0.0.1:8000`



API documentation: `http://127.0.0.1:8000/docs`



\### 3. Set up the frontend



Open another terminal:



```bash

cd frontend

npm install

npm run dev

```



\### 4. Start the local blockchain



Open another terminal:



```bash

npm --prefix smart-contracts install

npm --prefix smart-contracts run node

```



Deploy the smart contract from another terminal:



```bash

npm --prefix smart-contracts run compile

npm --prefix smart-contracts run deploy

```



\## 📊 Model Performance



The AI model achieved 97.33% accuracy on the held-out test dataset. Performance can vary depending on message content and dataset characteristics.



\## 🎓 Academic Project



\*\*Project Name:\*\* CipherChain – AI-Powered Secure Messaging with Blockchain Integration



\*\*University:\*\* Presidency University



\*\*Department:\*\* Computer Science and Engineering (Blockchain)



\*\*Academic Year:\*\* 2026–2027



\*\*Developed by:\*\*

\- Rakesh B G – 20241CBC0069

\- Sharana Basava I Javali – 20241CBC0052



\## ⚠️ Disclaimer



This project is developed for academic and educational purposes. The blockchain configuration currently uses a local development network and is not a production deployment. The system should undergo further security testing before real-world deployment.

