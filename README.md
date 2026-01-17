# **AyuSahayak - An AI Assisted, Multi Module, Trust Centric Rural Healthcare System**



##### **Problem Statement**



* Practicing medicine without MBBS and registration is illegal in Telangana; TSMC has filed multiple FIRs against RMP 'quacks’ and still continues statewide raids.
* Yet, every single day 1000s of villagers depend on these unqualified RMPs due to cost, distance, time and 24x7 access, causing unsafe treatments, misdiagnosis, and even deaths.
* Due to this high dependency on RMPs, nearby city hospitals lose patients \& revenue. 



##### **Proposed Solution**



* AyuSahayak is an hospital supporting tool and nurse decision supporting tool, nearby city hospitals launch their own branded micro-clinics.
* It implements trust triangle workflow linking remote hospital doctor and on-site nurse and village patients. 
* Village nurse is first contact : takes vitals, collects symptom data, uses AyuSahayak platform, and delivers in-person, trusted care.
* Supports a multi-module healthcare platform: distinct modules tailored for skin, wound, and rural care scenarios.
* Human-in-the-loop: AI modules only assist clinical staff; final prescription is written \& signed by remote-hospital-doctor reviewing AI assistance.





###### **Skin Care AI Module \& Wound Care AI Module :**

A **multimodal triage** system where a raw-image is an input to CNN, CNN predicts probable skin conditions, **semantic-normalized symptoms** are fused with image features, and **RAG** retrieves clinical guidelines, generates targeted, **differentiating symptom-based follow-up questions** to accurately identify the exact disease.



###### **Rural Care AI Module (Infectious \& Chronic Disease Management) :** 

1. **Multi-Agent Architecture** – Modular agents (Symptom Collector, Complexity, PCP(Primary Care Physician), MDT(Multi-Disciplinary Team), with clearly bounded responsibilities.
2. **Google Gemini embeddings (models/text-embedding-004) model** for symptom clustering, intent understanding, template matching, and semantic validation.



* **Symptom Collector Agent** performs structured intake with targeted, differentiating follow-up questions and red-flag prioritization using semantic clustering, rule-based question sequencing, negative-confirmation handling, and intent-aware GUARDRAILS(ensure accurate intake, safe outputs, and ethical boundaries).
* **Complexity Agent** triages cases (low / medium / high) using symptoms + vitals ,using text embeddings, vitals feature vectors, RandomForest classification, and hard safety overrides ; High-risk cases are immediately escalated to hospital.
* **PCP Agent** handles low-risk cases with rule-based, guideline-anchored care plans using syndrome matching, deterministic clinical templates, WHO-style RAG snippets, and strict medicine allow-lists.
* **MDT Agent** manages medium-risk cases via a virtual specialist opinions(AI cardio / pulmo / gastro / pediatric / neuro) using rule-based specialist selection, Google text-embedding-004 template similarity matching, deterministic opinion merging, and escalation-focused consensus logic.
* **Response Simplifier Agent** converts clinical output into culturally appropriate, nurse-friendly steps using a tightly sandboxed LLM from Google (Gemini) only for language simplification.





*Research \& Evidence of the problem :* https://drive.google.com/file/d/1Kn8kLH33qjw2gkzZ97ZNv7Ln-ChMFJFT/view?usp=sharing

*Detailed Presentation Deck :* https://docs.google.com/presentation/d/1Ke\_j5VJSoGelcyiE8RlgwjSIXuNmxVhp/edit?usp=sharing\&ouid=105871729050611763318\&rtpof=true\&sd=true









