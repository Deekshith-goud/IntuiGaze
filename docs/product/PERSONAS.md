# EyeNav — User Personas

**Document Version:** 1.0  
**Status:** Research-Validated  
**Owner:** UX Research Team  
**Last Updated:** 2024-Q4  

---

## Persona Development Methodology

These personas were developed through:
1. Literature review of assistive technology user research
2. Interviews with occupational therapists and AAC specialists
3. Analysis of existing Tobii Dynavox user feedback (public reviews, forums)
4. Desk research on disability community needs and preferences

---

## Persona 1 — Marcus, 34, ALS Patient

### Background
Marcus was a software architect at a cloud computing firm before being diagnosed with ALS at age 31. He lives with his partner in Seattle. He has two young children.

### Current Condition
- Upper limb weakness: Cannot use mouse or keyboard
- Speech: Mildly affected (can still speak but fatigues quickly)
- Vision: Normal
- Cognition: Fully intact

### Current Setup
- Tobii Dynavox with gaze control ($9,000 — paid by insurance)
- Eye tracking configured to select AAC communication symbols
- Limited success using gaze for computer navigation
- Frustrated that eye tracking accuracy degrades when he is tired

### Goals
- Work from home independently as long as possible
- Write code again (even slowly)
- Navigate the web, manage emails, video call family
- Feel independent, not dependent

### Pain Points
- Fatigue causes gaze drift → accidental commands
- Re-calibration required every 1–2 hours (stressful)
- Software options very limited — mostly designed for AAC, not productivity
- Cannot use standard software without extensive configuration
- Device costs are enormous barrier for users without insurance

### Quote
> "I want to type one line of code before I lose the ability to do anything with my hands. But the current tools aren't made for software developers. They're made for caregivers to help patients say 'yes' or 'no'."

### EyeNav Relevance
- **Fatigue adaptation** is a primary requirement Marcus validates
- **Intent system** prevents accidental commands when gaze drifts
- **Software-only** removes $9,000 hardware barrier
- **Code editor navigation** is a differentiated use case

---

## Persona 2 — Priya, 22, Quadriplegic Student

### Background
Priya sustained a C4-level spinal cord injury in a car accident at 17. She is now completing a computer science degree at university. She lives in university housing with an attendant.

### Current Condition
- No functional use of arms or legs
- Speech: Normal
- Vision: Normal
- Cognition: Fully intact, academically high-performing

### Current Setup
- Head pointer mouse
- Voice control (Dragon NaturallySpeaking)
- Some eye gaze use for scrolling only
- University accessibility office provides equipment

### Goals
- Complete CS degree independently
- Write code competitively
- Navigate web and apps without voice (voice is tiring and not private in library)
- Eventually work as a software engineer

### Pain Points
- Voice commands are not private (classmates stare)
- Head pointer is imprecise for small UI targets
- Eye gaze (limited) only works for scrolling, not navigation
- No solution works in all lighting conditions
- Eyes fatigue after 4–5 hours of screen use

### Quote
> "I have to choose between my privacy or being able to use my computer. Voice control means everyone in the library knows what I'm doing. I just want to use my laptop quietly like everyone else."

### EyeNav Relevance
- **Silent operation** — no audio needed
- **Multi-modal confirmation** prevents accidental selection in public
- **Fatigue detection** reduces error rate in long study sessions
- **CS-specific workflows** (code editor, terminal navigation)

---

## Persona 3 — Dr. Aisha, 45, Robotic Surgeon

### Background
Aisha is a robotic and laparoscopic surgeon at a major academic medical center. She leads a team of 8 in complex minimally invasive procedures.

### Current Condition
- No disability — full motor function
- Hands are occupied during surgery
- Eyes are primary operational channel during procedures

### Current Setup
- Verbal commands to scrub techs
- Foot pedals for some instrument control
- Looking away from surgical field to adjust settings is risky

### Goals
- Adjust zoom, lighting, irrigation without breaking sterile field
- Control surgical suite HUD with eyes
- Reduce reliance on scrub tech for routine adjustments
- Log surgical events hands-free

### Pain Points
- Interrupting flow to request adjustments increases procedure time
- No gaze control for surgical displays exists in commercial products
- Safety-critical context — false positives could be dangerous
- Different head poses during procedures (leaning forward, sideways)

### Quote
> "Every time I need to adjust the camera angle or change instrument settings, I either call out and wait, or break sterile field. We're in 2024. This should be solvable."

### EyeNav Relevance
- **Surgical suite use case** demands extreme false-positive safety
- **Sterile environment** makes software-only critical
- **Head pose variation** during procedures tests robustness
- **High-value enterprise** market with strong willingness to pay

---

## Persona 4 — Tomás, 58, Parkinson's Disease

### Background
Tomás is a retired teacher with Parkinson's disease. He lives alone in Madrid. His tremors make mouse and touch interaction extremely difficult.

### Current Condition
- Moderate Parkinson's — significant hand tremor
- Speech: Mild dysarthria (voice recognition unreliable)
- Vision: Normal (glasses)
- Cognition: Intact

### Current Setup
- Large-key keyboard
- Trackball mouse (reduces tremor impact somewhat)
- Some voice control (unreliable due to dysarthria)

### Goals
- Video call family (grandchildren)
- Read news and books online
- Manage finances and appointments
- Maintain independence as disease progresses

### Pain Points
- Tremor causes mouse cursor to shake — imprecise selection
- Standard voice control doesn't recognize his dysarthric speech
- Eye tracking products require hardware he can't set up alone
- Configuration is too complex for non-technical users

### Quote
> "My mind is completely clear. I know exactly what I want to do. My hands just won't cooperate anymore."

### EyeNav Relevance
- **Non-technical user** — setup must be extremely simple
- **Glasses support** is critical
- **Dysarthria** makes voice control non-viable → eye gaze as primary
- **Autonomous setup** — must work without technical assistance

---

## Persona 5 — Kenji, 29, AR Game Developer

### Background
Kenji is a game developer at an indie studio building AR experiences for Meta Quest and Apple Vision Pro.

### Current Condition
- No disability
- Uses AR/VR headsets 6–8 hours daily
- Familiar with gaze-based interaction APIs

### Goals
- Build more natural AR interaction beyond controller gestures
- Add gaze-based intent to game UI (look at item → context menu appears)
- Cross-platform gaze input handling (different headset APIs are fragmented)

### Pain Points
- Meta, Apple, Pico — all have different gaze APIs
- No cross-platform abstraction layer for gaze intent
- Current systems only provide coordinates — intent logic must be built from scratch per app
- No open-source intent classification library available

### Quote
> "I'm building an AR inventory system. The user should just *look* at an item and think 'pick this up' and it should happen. But right now I have to write a state machine per headset. It's exhausting."

### EyeNav Relevance
- **SDK consumer** — will use EyeNav SDK as intent abstraction layer
- **Cross-platform** unification is core requirement
- **AR-native** design needed for headset contexts
- Represents a large developer community with similar needs

---

## Persona 6 — Naledi, 16, Cerebral Palsy

### Background
Naledi has spastic cerebral palsy affecting all four limbs. She is in secondary school in Johannesburg. She communicates using AAC and eye gaze.

### Current Condition
- Severe physical disability — eye gaze is primary interaction modality
- Cognition: Fully intact, strong student
- Using Tobii Dynavox eye tracker ($9,000 USD — family struggling with cost)

### Goals
- Use standard apps (social media, YouTube, WhatsApp) with eye gaze
- Not feel excluded from technology her peers use
- Be understood by friends without requiring AAC for every interaction

### Pain Points
- Current eye gaze devices designed for clinical communication, not teen life
- Social media apps not accessible via gaze
- Device is bulky and stigmatizing to bring to school
- African market has no local support for Tobii products
- Cost is catastrophic for the family

### Quote
> "All my friends are on TikTok. My device can help me say 'yes' or 'no.' That's not the same thing."

### EyeNav Relevance
- **Cost barrier** — EyeNav on a phone/tablet dramatically reduces cost
- **Standard app navigation** — primary use case
- **Low-income market** — mission-critical affordability
- **Mobile-first** — phone as eye tracking device unlocks global access

---

## Persona Summary Table

| Persona | Age | Condition | Primary Need | Device | Market Segment |
|---|---|---|---|---|---|
| Marcus | 34 | ALS | Productivity | Desktop | Assistive |
| Priya | 22 | Quadriplegia | Silent control | Laptop | Assistive |
| Dr. Aisha | 45 | None (surgical) | Sterile HCI | Display | Enterprise |
| Tomás | 58 | Parkinson's | Simple gaze control | Desktop | Assistive |
| Kenji | 29 | None (developer) | Intent SDK | AR Headset | Developer |
| Naledi | 16 | Cerebral Palsy | Social app access | Phone/Tablet | Assistive/Consumer |

---

## Design Implications

1. **Zero-tolerance for false positives** — Every persona except Kenji is harmed by accidental commands
2. **Setup simplicity** — Tomás and Naledi cannot troubleshoot complex systems
3. **Glasses support** — Tomás (glasses), Priya (varies) — non-negotiable
4. **Fatigue handling** — Marcus, Priya, Tomás all experience ocular fatigue
5. **Cost sensitivity** — Marcus has insurance, Naledi does not — pricing must accommodate both
6. **Privacy** — Priya's library context makes silent operation essential
7. **Standard app compatibility** — Naledi's TikTok need proves we cannot rely on apps being specially designed for us
