# Body Measurement Feature - Implementation Plan

## Executive Summary

Build a mobile fitness app feature that captures skeletal dimensions using AI pose estimation + depth sensing to predict exercise-specific biomechanical advantages. One-time measurement capture with persistent storage and exercise recommendations.

---

## Phase 1: Technology Stack Selection

### Pose Estimation
**Primary: MediaPipe BlazePose**
- 33 3D landmarks with real-time performance on mobile
- Native iOS/Android support via ML Kit
- Provides 2D pixel coordinates + normalized 3D coordinates
- Proven accuracy for joint detection (shoulders, elbows, wrists, hips, knees, ankles)

**Implementation Options:**
- **iOS:** QuickPose SDK (wrapper around MediaPipe) or Google ML Kit
- **Android:** Google ML Kit Pose Detection API
- **Cross-platform:** React Native + `react-native-google-mlkit` or Flutter + `google_ml_kit`

### Depth Sensing / Calibration
**Hybrid Approach (decreasing dependency order):**

1. **ARCore Depth API (Android) / ARKit (iOS)** - when available
   - Depth-from-motion algorithm using single RGB camera
   - Accurate 0.5m-5m range
   - Best when device moved during capture

2. **Reference Object Method** - fallback/enhancement
   - User places known-size object (credit card: 85.6×53.98mm, standard water bottle, etc.)
   - Detect object in frame alongside pose
   - Calculate pixels-per-millimeter ratio

3. **User Height Input** - baseline calibration
   - User enters known height
   - Scale all measurements proportionally from head-to-ankle distance

### Mobile Framework
**Recommendation: React Native**

**Rationale:**
- Mature ML Kit bindings (`react-native-google-mlkit`)
- ARCore/ARKit wrappers available
- Faster iteration for MVP
- Strong camera API support
- JavaScript ecosystem for data processing

**Alternative: Flutter**
- Better performance for animations/UI
- Requires more native bridging for ML features
- Consider if team has Dart expertise

### Backend/Storage
- **Local:** SQLite/Realm for measurement persistence
- **Cloud (optional):** Firebase Firestore for cross-device sync
- **Format:** JSON schema for skeletal dimensions + metadata

---

## Phase 2: Measurement Workflow

### 2.1 Photo Capture Flow

**Guided Capture Sequence (3 poses):**

1. **Front-facing stance** (arms at sides, T-pose)
   - Detects: shoulder width, arm segments (fingertip→wrist→elbow→shoulder), torso length (shoulder→hip)

2. **Side-facing stance** (profile view)
   - Detects: torso depth, femur length (hip→knee), tibia length (knee→ankle)
   - Critical for femur/torso ratio (squat predictor)

3. **Arms extended forward** (depth reference)
   - Validates depth measurements
   - Confirms arm segment calculations

**Capture Requirements:**
- Distance: 2-3 meters from camera (ARCore optimal range)
- Lighting: Well-lit, even illumination (detect via brightness histogram)
- Background: Uncluttered (pose confidence threshold >0.8)
- Device position: Mounted at chest height (tripod/shelf)

**Real-time Feedback:**
- Skeleton overlay showing detected landmarks
- Confidence score per landmark (reject if <0.7)
- Distance indicator (too close/far)
- Pose correctness checklist (arms straight, weight even, facing camera)

### 2.2 Pose Detection → Dimension Calculation

**MediaPipe Landmarks Used:**
```
Shoulders: 11 (left), 12 (right)
Elbows: 13 (left), 14 (right)
Wrists: 15 (left), 16 (right)
Hips: 23 (left), 24 (right)
Knees: 25 (left), 26 (right)
Ankles: 27 (left), 28 (right)
Index fingers: 19 (left), 20 (right)
```

**Segment Calculations (Euclidean distance in 3D):**
```
fingertip_to_wrist = distance(landmark[19/20], landmark[15/16])
wrist_to_elbow = distance(landmark[15/16], landmark[13/14])
elbow_to_shoulder = distance(landmark[13/14], landmark[11/12])
shoulder_to_hip = distance(landmark[11/12], landmark[23/24])
hip_to_knee = distance(landmark[23/24], landmark[25/26])
knee_to_ankle = distance(landmark[25/26], landmark[27/28])
shoulder_width = distance(landmark[11], landmark[12])
torso_length = avg(left_shoulder_to_hip, right_shoulder_to_hip)
```

**Average left/right sides**, flag asymmetry >5% for user review.

### 2.3 Calibration Methods

**Priority 1: ARCore/ARKit Depth**
- Extract depth map during capture
- Map depth values to pose landmarks
- Calculate real-world distances using depth + camera intrinsics

**Priority 2: Reference Object**
- Detect credit card (or standard object) via object detection model
- Known dimensions: 85.6mm × 53.98mm
- Calculate scale: `real_mm / pixel_distance`
- Apply scale to all pose segments

**Priority 3: User Height**
- Input: User height (cm)
- Measure: Head-to-ankle distance in pixels (landmark[0] to landmark[27/28])
- Scale factor: `user_height_cm / head_to_ankle_pixels`

**Validation:**
- Cross-check calibration methods (if multiple available)
- Anatomical plausibility checks (femur typically 26% of height)
- Confidence scoring based on method used

---

## Phase 3: Biomechanics Mapping

### 3.1 Key Ratios & Exercise Predictions

**Squat Advantage:**
- **Femur-to-torso ratio** (primary): `femur_length / torso_length`
  - Low ratio (<0.9): Advantage (short femurs, upright torso easier)
  - High ratio (>1.1): Disadvantage (long femurs increase moment arm)
- **Leg-to-height ratio**: `(femur + tibia) / total_height`
  - High ratio (>0.49): Longer ROM, harder depth

**Deadlift Advantage:**
- **Arm-to-torso ratio**: `total_arm_length / torso_length`
  - High ratio (>1.2): Advantage (long arms reduce ROM)
- **Torso-to-height ratio**: `torso_length / total_height`
  - High ratio (>0.32): Disadvantage (more horizontal back angle)

**Bench Press Advantage:**
- **Forearm-to-upper-arm ratio**: `(wrist_to_elbow) / (elbow_to_shoulder)`
  - Ratio ~1.0: Balanced leverages
  - Short forearms: Advantage at lockout
- **Arm length**: Total arm length
  - Shorter arms: Less ROM, typically advantageous

**Overhead Press:**
- **Total arm length**: Longer ROM = harder
- **Shoulder width**: Wider base may help stability

**Bicep Curls:**
- **Forearm length**: Longer forearm = longer moment arm = harder
- **Forearm-to-upper-arm ratio**: Lower ratio favors curls

### 3.2 Scoring System

**Per-exercise score (0-100):**
- Calculate percentile based on population norms (or app user dataset)
- 50 = average leverage
- >70 = biomechanical advantage
- <30 = biomechanical disadvantage

**Recommendations:**
- Tier 1 (>70): "Excellent leverage for [exercise] - prioritize this in programming"
- Tier 2 (40-70): "Average leverage - standard programming applies"
- Tier 3 (<40): "Challenging leverages - focus on technique, consider variations"

**Exercise Variations:**
- Short arms + long femurs → Suggest sumo deadlift over conventional
- Long femurs → Suggest front squat, low-bar squat, box squat
- Long arms → Emphasize deadlift/rowing strength

### 3.3 Research-Backed Ratios (Implementation Constants)

Based on research findings:
```javascript
const BIOMECHANICS_THRESHOLDS = {
  squat: {
    femurToTorso: { advantage: 0.9, disadvantage: 1.1 },
    legToHeight: { disadvantage: 0.49 }
  },
  deadlift: {
    armToTorso: { advantage: 1.2 },
    torsoToHeight: { disadvantage: 0.32 }
  },
  benchPress: {
    forearmToUpperArm: { optimal: 1.0, tolerance: 0.1 }
  }
}
```

---

## Phase 4: Data Model

### 4.1 Measurement Schema

```typescript
interface BodyMeasurements {
  id: string;
  userId: string;
  capturedAt: timestamp;
  version: string; // schema version for migrations

  calibration: {
    method: 'arcore' | 'arkit' | 'reference_object' | 'user_height';
    confidenceScore: number; // 0-1
    scaleFactorMmPerPixel: number;
    userHeightCm?: number;
    referenceObjectType?: string;
  };

  rawData: {
    frontPose: PoseLandmarks; // 33 landmarks × 3 coords
    sidePose: PoseLandmarks;
    armsExtendedPose: PoseLandmarks;
    depthMaps?: DepthMap[]; // if ARCore/ARKit used
  };

  segments: {
    // All in millimeters
    fingerTipToWrist: { left: number; right: number };
    wristToElbow: { left: number; right: number };
    elbowToShoulder: { left: number; right: number };
    shoulderToHip: { left: number; right: number };
    hipToKnee: { left: number; right: number };
    kneeToAnkle: { left: number; right: number };
    shoulderWidth: number;
    torsoLength: number;
    totalHeight: number;

    // Asymmetry flags
    asymmetry: {
      arms: number; // percentage difference
      legs: number;
    };
  };

  derivedRatios: {
    femurToTorso: number;
    armToTorso: number;
    forearmToUpperArm: number;
    legToHeight: number;
    torsoToHeight: number;
  };

  exerciseScores: {
    squat: ExerciseScore;
    deadlift: ExerciseScore;
    benchPress: ExerciseScore;
    overheadPress: ExerciseScore;
    bicepCurl: ExerciseScore;
  };
}

interface ExerciseScore {
  score: number; // 0-100
  tier: 'advantage' | 'average' | 'disadvantage';
  primaryFactors: string[]; // e.g., ["Short femurs", "Long torso"]
  recommendations: string[];
}

interface PoseLandmarks {
  landmarks: Array<{ x: number; y: number; z: number; visibility: number }>;
  worldLandmarks: Array<{ x: number; y: number; z: number }>; // real-world coords
  confidenceScore: number;
}
```

### 4.2 Storage Strategy

**Local-first:**
- SQLite table: `body_measurements`
- One record per user (update on recapture)
- Store raw pose data for future algorithm improvements

**Cloud sync (optional Phase 2):**
- Firebase Firestore: `/users/{userId}/measurements/{measurementId}`
- Enable cross-device access
- Analytics on population distributions (anonymized)

---

## Phase 5: UI/UX Flow

### 5.1 Measurement Capture Wizard

**Step 1: Introduction**
- Explain purpose (one-time setup, 5 minutes)
- Requirements: tripod/phone stand, 2-3m space, good lighting, form-fitting clothes

**Step 2: Calibration Choice**
- Option A: Place credit card in view (show diagram)
- Option B: Enter your height (less accurate)
- Auto-detect AR capabilities (suggest ARCore/ARKit if available)

**Step 3: Front Pose**
- Live camera with skeleton overlay
- Checklist indicators:
  - ✓ Distance correct (ARCore feedback)
  - ✓ Lighting good (>50 lux)
  - ✓ Full body visible
  - ✓ Arms straight
  - ✓ Confidence >0.8
- "Hold still" countdown (3 sec) → Capture

**Step 4: Side Pose**
- Instruction: "Turn 90° to your right"
- Same checklist validation
- Capture

**Step 5: Arms Extended**
- Instruction: "Extend arms forward, parallel to ground"
- Capture

**Step 6: Processing**
- Progress bar: "Analyzing measurements..."
- Backend: Run calculations (segments → ratios → scores)

**Step 7: Results Dashboard**
- Visual representation: 3D body model with segment lengths labeled
- Exercise cards: Squat/Deadlift/Bench with scores
- Expandable details: "Why this score?" (show ratios)
- CTA: "See recommended program"

### 5.2 Results Screen Design

**Visual Components:**
- Radar chart: Exercise scores (5 exercises)
- Body diagram: Color-coded segments (green=advantage, yellow=average, red=disadvantage)
- Top recommendation card: "Your strongest lift: Deadlift (Score: 78)"
- List view: All exercises with tier badges

**Actions:**
- Retake measurement
- Share results (anonymized)
- Export PDF report

---

## Phase 6: Accuracy Validation

### 6.1 Validation Protocol

**Ground Truth Comparison:**
- Test on 50 users with manual tape measurements by trainer
- Compare automated vs. manual for each segment
- Target: <3% error for major segments (femur, torso, arm)

**Calibration Method Ranking:**
- ARCore/ARKit: Expected ±2-3% error
- Reference object: ±3-5% error
- User height: ±5-10% error

**Pose Detection Quality:**
- Reject captures with average landmark confidence <0.7
- Require all critical landmarks visible (shoulders, hips, knees, ankles)
- Flag asymmetry >5% for user verification

### 6.2 Error Handling

**Common Failures:**
- Insufficient lighting → Guide to move to better location
- Too close/far → Distance indicator with arrows
- Partial body occlusion → "Step back, ensure full body visible"
- Low confidence landmarks → "Hold pose steadier, remove baggy clothing"

**Fallback Strategy:**
- If AR depth fails: Automatically switch to reference object prompt
- If reference object fails: Fall back to user height input
- Store calibration method used for quality assessment

---

## Phase 7: Implementation Phases

### MVP (6-8 weeks)

**Sprint 1-2: Core Infrastructure**
- React Native project setup
- Integrate ML Kit Pose Detection (Android + iOS)
- Camera capture screen with live pose overlay
- Landmark confidence validation

**Sprint 3: Calibration**
- User height input flow
- Reference object detection (credit card via object detection model)
- Scale calculation logic
- Unit tests for segment distance calculations

**Sprint 4: Measurement Logic**
- Segment distance algorithms
- Ratio calculations
- Exercise scoring engine
- Data model + SQLite schema

**Sprint 5: UI Polish**
- Guided capture wizard (3 poses)
- Results dashboard
- Retake flow
- Basic error handling

**Sprint 6: Validation**
- Internal testing with 20 users
- Manual measurement comparison
- Accuracy tuning
- Bug fixes

### Phase 2 (4-6 weeks)

- ARCore/ARKit depth integration
- Advanced object detection for reference objects
- Exercise recommendation engine
- Program generation based on scores
- Cloud sync (Firebase)

### Phase 3 (Optional Enhancements)

- Video-based measurement (motion analysis)
- Multi-person comparison (percentile rankings)
- Progress tracking (measure every 3-6 months for proportional changes)
- Integration with workout logging
- Custom exercise database with biomechanics tags

---

## Technical Dependencies & Risks

### Dependencies
1. **MediaPipe/ML Kit availability** → Mitigated: Mature, production-ready
2. **AR framework support** → Mitigated: ARCore works on most Android devices (2018+), ARKit on iOS 11+
3. **Camera permissions** → Standard mobile permission flow
4. **Reference object detection** → Use TensorFlow Lite Object Detection (MobileNet)

### Risks
- **Accuracy concerns** → Mitigated: Multi-method calibration, validation protocol
- **User compliance (setup difficulty)** → Mitigated: Clear instructions, real-time feedback
- **Body composition changes** → Accept: Measurements are skeletal (bone lengths don't change)
- **Clothing interference** → Require form-fitting attire in instructions
- **Device fragmentation** → Test on range of phones, graceful degradation

---

## Technical Stack Summary

| Component | Technology | Alternatives |
|-----------|-----------|--------------|
| Mobile Framework | React Native | Flutter |
| Pose Estimation | Google ML Kit (MediaPipe) | TensorFlow Lite Pose Detection |
| Depth Sensing | ARCore/ARKit Depth API | Stereo camera (limited devices) |
| Reference Detection | TensorFlow Lite Object Detection | Custom OpenCV template matching |
| Local Storage | SQLite (react-native-sqlite-storage) | Realm, WatermelonDB |
| Cloud Storage | Firebase Firestore | AWS DynamoDB, Supabase |
| 3D Visualization | Three.js / React Three Fiber | Babylon.js |

---

## Success Metrics

**Technical:**
- Measurement accuracy: <5% error vs. manual tape
- Capture success rate: >85% first attempt
- Processing time: <10 seconds after final capture
- Crash-free rate: >99.5%

**User Experience:**
- Completion rate: >70% of users who start capture
- Time to complete: <8 minutes average
- Retake rate: <30%

**Business:**
- User satisfaction with recommendations: >4.0/5.0
- Feature retention: Users who reference measurements in workouts (>50%)

---

## Quick Start Decision Tree

### Before Full Implementation

**Hackathon Validation (2 weeks):**
1. Build minimal calibration (user height input only)
2. Single pose capture (front-facing)
3. Calculate femur/torso ratio → squat score only
4. Simple results screen
5. Test with 50 beta users
6. Measure: completion rate, score correlation with actual squat performance

**If validation succeeds (>60% completion, positive feedback):**
- Proceed with full MVP (6-8 weeks)

**If validation fails:**
- Pivot to simpler measurement (manual input with guided instructions)
- Or abandon feature, focus on other differentiators

---

## Appendix: Research References

### Biomechanics Studies
- Femur length impact on squat mechanics (Escamilla et al., 2001)
- Arm length advantages in deadlift (Hales et al., 2009)
- Anthropometric predictors of bench press performance (Mayhew et al., 1992)

### Pose Estimation Accuracy
- MediaPipe BlazePose validation (Bazarevsky et al., 2020)
- ARCore Depth API accuracy benchmarks (Google I/O 2020)
- Mobile pose estimation in fitness applications (Various industry reports)

### Population Anthropometry Norms
- CDC anthropometric reference data
- NHANES body measurement data
- Sports science limb ratio databases
