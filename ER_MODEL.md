# Entity-Relationship Model: Pediatric Cardiac Screening System

## Overview
This ER model represents the data architecture for a multimodal pediatric cardiac screening system that combines three modalities (Heart Sound/PCG, Cardiac Ultrasound, Chest X-Ray) using a Gated Multimodal Unit (GMU) fusion approach.

---

## Entities

### 1. PATIENT
Central entity representing a pediatric patient undergoing cardiac screening.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `patient_id` | VARCHAR(50) | PK, NOT NULL | Unique patient identifier |
| `age_months` | INT | | Age at time of screening |
| `sex` | ENUM('M','F') | | Biological sex |
| `weight_kg` | DECIMAL(5,2) | | Patient weight |
| `height_cm` | DECIMAL(5,2) | | Patient height |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMP | ON UPDATE NOW() | Last modification time |

---

### 2. SCREENING_SESSION
Represents a single screening visit/episode for a patient.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `session_id` | UUID | PK, NOT NULL | Unique session identifier |
| `patient_id` | VARCHAR(50) | FK → PATIENT, NOT NULL | Patient reference |
| `session_date` | DATE | NOT NULL | Date of screening |
| `clinical_notes` | TEXT | | Clinician observations |
| `referral_reason` | VARCHAR(200) | | Why screening was ordered |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

---

### 3. MODALITY (Abstract/Supertype)
Base entity for all imaging/audio modalities.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `modality_id` | UUID | PK, NOT NULL | Unique modality record ID |
| `session_id` | UUID | FK → SCREENING_SESSION, NOT NULL | Session reference |
| `modality_type` | ENUM('AUDIO','ULTRASOUND','XRAY') | NOT NULL | Discriminator |
| `file_path` | VARCHAR(500) | NOT NULL | Path to stored file |
| `file_format` | VARCHAR(20) | | e.g., 'wav', 'dcm', 'png', 'jpg' |
| `acquisition_device` | VARCHAR(100) | | Device/model used |
| `acquisition_params` | JSON | | Device-specific parameters |
| `quality_score` | DECIMAL(3,2) | CHECK (0-1) | Automated quality assessment |
| `is_usable` | BOOLEAN | DEFAULT TRUE | Whether modality passed QC |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

---

### 4. AUDIO_RECORDING (Subtype of MODALITY)
Heart sound (PCG) recordings.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `modality_id` | UUID | PK, FK → MODALITY | Inherited PK |
| `duration_sec` | DECIMAL(6,2) | | Recording duration |
| `sample_rate` | INT | | Original sample rate (Hz) |
| `num_channels` | INT | | Number of audio channels |
| `auscultation_site` | ENUM('A','P','T','M','Erb') | | Aortic, Pulmonic, Tricuspid, Mitral, Erb's point |
| `body_position` | ENUM('supine','sitting','left_lateral') | | Patient position during recording |
| `heart_rate_bpm` | INT | | Estimated heart rate |

---

### 5. ULTRASOUND_STUDY (Subtype of MODALITY)
Pediatric echocardiography still images.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `modality_id` | UUID | PK, FK → MODALITY | Inherited PK |
| `view_type` | ENUM('PLAX','PSAX','AP4','AP5','SC','IVC','SUBCOSTAL') | | Standard echo views |
| `frame_number` | INT | | Frame index in cine loop |
| `total_frames` | INT | | Total frames in acquisition |
| `probe_frequency_mhz` | DECIMAL(4,1) | | Transducer frequency |
| `depth_cm` | DECIMAL(4,1) | | Imaging depth |
| `gain_db` | INT | | Gain setting |

---

### 6. XRAY_STUDY (Subtype of MODALITY)
Chest X-ray images.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `modality_id` | UUID | PK, FK → MODALITY | Inherited PK |
| `view_type` | ENUM('PA','AP','LATERAL','OBlique') | | Projection view |
| `laterality` | ENUM('frontal','lateral') | | Image orientation |
| `kvp` | DECIMAL(5,1) | | Kilovoltage peak |
| `mas` | DECIMAL(6,1) | | Milliampere-seconds |
| `sid_cm` | INT | | Source-to-image distance |
| `grid_used` | BOOLEAN | | Whether anti-scatter grid was used |

---

### 7. DIAGNOSIS_LABEL
Ground truth labels for supervised learning.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `label_id` | UUID | PK, NOT NULL | Unique label identifier |
| `session_id` | UUID | FK → SCREENING_SESSION, NOT NULL | Session reference |
| `label_source` | ENUM('CATHETERIZATION','SURGERY','ECHO_CONFIRMED','CLINICAL_FOLLOWUP','EXPERT_CONSENSUS') | NOT NULL | How diagnosis was established |
| `primary_diagnosis` | ENUM('NORMAL','CHD') | NOT NULL | Binary: 0=Normal, 1=CHD |
| `specific_defects` | JSON | | Array of specific defects (VSD, ASD, TOF, etc.) |
| `severity` | ENUM('MILD','MODERATE','SEVERE') | | For CHD cases |
| `labeled_by` | VARCHAR(100) | | Clinician/expert identifier |
| `labeled_at` | TIMESTAMP | NOT NULL | When label was assigned |
| `confidence` | DECIMAL(3,2) | CHECK (0-1) | Label confidence |

---

### 8. SPECIALIST_MODEL
Individual modality-specific deep learning models (Phase-1).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `model_id` | UUID | PK, NOT NULL | Unique model identifier |
| `model_name` | VARCHAR(50) | NOT NULL, UNIQUE | e.g., 'CRNN_Audio', 'NTSNet_US', 'EfficientNet_XRay' |
| `modality_type` | ENUM('AUDIO','ULTRASOUND','XRAY') | NOT NULL | Associated modality |
| `architecture` | VARCHAR(100) | | e.g., 'CRNN2D', 'NTSNet', 'EfficientNetV2-S' |
| `backbone` | VARCHAR(50) | | e.g., 'ResNet18', 'ResNet50', 'EfficientNetV2-S' |
| `embed_dim` | INT | DEFAULT 512 | Output embedding dimension |
| `num_parameters` | BIGINT | | Total trainable parameters |
| `input_shape` | VARCHAR(50) | | e.g., '(1,64,256)', '(3,224,224)' |
| `training_config` | JSON | | Hyperparameters used |
| `checkpoint_path` | VARCHAR(500) | | Path to saved weights |
| `version` | VARCHAR(20) | | Model version |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration time |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether deployed |

---

### 9. SPECIALIST_TRAINING_RUN
Training history for each specialist model (Phase-1).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `run_id` | UUID | PK, NOT NULL | Unique training run ID |
| `model_id` | UUID | FK → SPECIALIST_MODEL, NOT NULL | Model reference |
| `split` | ENUM('train','val','test') | NOT NULL | Data split |
| `epoch` | INT | NOT NULL | Epoch number |
| `loss` | DECIMAL(10,6) | | Training/validation loss |
| `auc_roc` | DECIMAL(5,4) | | Area under ROC curve |
| `auc_pr` | DECIMAL(5,4) | | Area under PR curve |
| `accuracy` | DECIMAL(5,4) | | Classification accuracy |
| `sensitivity` | DECIMAL(5,4) | | True positive rate |
| `specificity` | DECIMAL(5,4) | | True negative rate |
| `f1_score` | DECIMAL(5,4) | | Harmonic mean of precision/recall |
| `learning_rate` | DECIMAL(10,8) | | LR at this epoch |
| `duration_sec` | INT | | Epoch duration |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Log timestamp |

---

### 10. EMBEDDING
512-dimensional feature vectors extracted by specialist models.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `embedding_id` | UUID | PK, NOT NULL | Unique embedding ID |
| `modality_id` | UUID | FK → MODALITY, NOT NULL | Source modality |
| `model_id` | UUID | FK → SPECIALIST_MODEL, NOT NULL | Extractor model |
| `embedding_vector` | VECTOR(512) / BLOB | NOT NULL | 512-dim embedding (float32) |
| `extracted_at` | TIMESTAMP | DEFAULT NOW() | Extraction timestamp |
| `inference_time_ms` | INT | | Model inference latency |

---

### 11. GMU_MODEL (Gated Multimodal Unit)
The Level-1 meta-learner that fuses specialist embeddings (Phase-2).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `gmu_id` | UUID | PK, NOT NULL | Unique GMU identifier |
| `gmu_name` | VARCHAR(50) | NOT NULL, UNIQUE | e.g., 'GMU_v1' |
| `audio_model_id` | UUID | FK → SPECIALIST_MODEL | Audio specialist (CRNN) |
| `us_model_id` | UUID | FK → SPECIALIST_MODEL | Ultrasound specialist (NTS-Net) |
| `xray_model_id` | UUID | FK → SPECIALIST_MODEL | X-Ray specialist (EfficientNet) |
| `gmu_hidden_dim` | INT | DEFAULT 512 | Per-modality gate projection dim |
| `mlp_hidden_dims` | JSON | | e.g., '[512, 256]' |
| `mlp_dropout` | DECIMAL(3,2) | DEFAULT 0.5 | MLP dropout rate |
| `modality_drop_p` | DECIMAL(3,2) | DEFAULT 0.2 | Modality dropout probability |
| `checkpoint_path` | VARCHAR(500) | | Path to saved GMU weights |
| `version` | VARCHAR(20) | | Model version |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration time |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether deployed |

---

### 12. GMU_TRAINING_RUN
Training history for the GMU fusion model (Phase-2).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `run_id` | UUID | PK, NOT NULL | Unique training run ID |
| `gmu_id` | UUID | FK → GMU_MODEL, NOT NULL | GMU reference |
| `split` | ENUM('train','val','test') | NOT NULL | Data split |
| `epoch` | INT | NOT NULL | Epoch number |
| `loss` | DECIMAL(10,6) | | BCEWithLogitsLoss |
| `auc_roc` | DECIMAL(5,4) | | Area under ROC curve |
| `auc_pr` | DECIMAL(5,4) | | Area under PR curve |
| `accuracy` | DECIMAL(5,4) | | Classification accuracy |
| `sensitivity` | DECIMAL(5,4) | | True positive rate |
| `specificity` | DECIMAL(5,4) | | True negative rate |
| `f1_score` | DECIMAL(5,4) | | Harmonic mean |
| `gate_audio_mean` | DECIMAL(5,4) | | Mean audio gate weight |
| `gate_us_mean` | DECIMAL(5,4) | | Mean ultrasound gate weight |
| `gate_xray_mean` | DECIMAL(5,4) | | Mean X-ray gate weight |
| `learning_rate` | DECIMAL(10,8) | | LR at this epoch |
| `duration_sec` | INT | | Epoch duration |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Log timestamp |

---

### 13. INFERENCE_RESULT
Results from running the full pipeline on a screening session.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `inference_id` | UUID | PK, NOT NULL | Unique inference ID |
| `session_id` | UUID | FK → SCREENING_SESSION, NOT NULL | Session reference |
| `gmu_id` | UUID | FK → GMU_MODEL, NOT NULL | Model used |
| `probability_chd` | DECIMAL(6,5) | CHECK (0-1) | P(CHD) from sigmoid(logit) |
| `predicted_label` | ENUM('PASS','REFER') | NOT NULL | 0=Pass, 1=Refer |
| `threshold_used` | DECIMAL(3,2) | DEFAULT 0.5 | Decision threshold |
| `gate_weights` | JSON | | Per-modality gate values: {audio, us, xray} |
| `modalities_present` | JSON | | Which modalities were available: {audio, us, xray} |
| `inference_time_ms` | INT | | Total pipeline latency |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Inference timestamp |

---

### 14. DATA_SPLIT
Train/Val/Test split assignments for reproducible experiments.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `split_id` | UUID | PK, NOT NULL | Unique split assignment ID |
| `session_id` | UUID | FK → SCREENING_SESSION, NOT NULL | Session reference |
| `split_name` | ENUM('train','val','test') | NOT NULL | Split assignment |
| `fold` | INT | DEFAULT 0 | Cross-validation fold (0 = single split) |
| `assigned_by` | VARCHAR(50) | | Strategy: 'random', 'patient_stratified', 'temporal' |
| `assigned_at` | TIMESTAMP | DEFAULT NOW() | Assignment time |

---

### 15. EXPLAINABILITY_OUTPUT
Grad-CAM and attention outputs for interpretability.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `explain_id` | UUID | PK, NOT NULL | Unique explanation ID |
| `inference_id` | UUID | FK → INFERENCE_RESULT, NOT NULL | Associated inference |
| `modality_type` | ENUM('AUDIO','ULTRASOUND','XRAY') | NOT NULL | Modality explained |
| `heatmap_path` | VARCHAR(500) | | Path to saved heatmap image |
| `heatmap_array` | BLOB | | Raw heatmap tensor (if stored) |
| `attention_weights` | JSON | | For audio: temporal attention weights |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Generation time |

---

## Relationships

```
PATIENT (1) ─────< (N) SCREENING_SESSION
SCREENING_SESSION (1) ─────< (N) MODALITY
MODALITY (1) ─────< (0..1) AUDIO_RECORDING
MODALITY (1) ─────< (0..1) ULTRASOUND_STUDY
MODALITY (1) ─────< (0..1) XRAY_STUDY

SCREENING_SESSION (1) ─────< (1) DIAGNOSIS_LABEL
SCREENING_SESSION (1) ─────< (1) DATA_SPLIT

MODALITY (1) ─────< (N) EMBEDDING
SPECIALIST_MODEL (1) ─────< (N) EMBEDDING
SPECIALIST_MODEL (1) ─────< (N) SPECIALIST_TRAINING_RUN

GMU_MODEL (N) ─────< (3) SPECIALIST_MODEL  (audio, us, xray)
GMU_MODEL (1) ─────< (N) GMU_TRAINING_RUN

SCREENING_SESSION (1) ─────< (N) INFERENCE_RESULT
GMU_MODEL (1) ─────< (N) INFERENCE_RESULT
INFERENCE_RESULT (1) ─────< (N) EXPLAINABILITY_OUTPUT
```

---

## Key Design Decisions

### 1. Modality Subtyping
- **Single-table inheritance** with discriminator `modality_type`
- Allows unified querying while preserving modality-specific attributes
- `is_usable` flag handles quality control (replaces NaN paths in CSVs)

### 2. Patient-Session-Modality Hierarchy
- One patient → multiple sessions (longitudinal tracking)
- One session → 0-3 modalities (missing modalities are explicit)
- Missing modality = no row in MODALITY table (not a NULL path)

### 3. Specialist → Embedding → GMU Pipeline
- **Phase-1**: SPECIALIST_MODEL trained independently per modality
- **Embeddings** extracted and stored (enables fast GMU training)
- **Phase-2**: GMU_MODEL trains on pre-computed embeddings

### 4. Modality Dropout Support
- GMU trained with random modality zeroing (`modality_drop_p`)
- Inference records which modalities were present (`modalities_present`)
- Gate weights logged for interpretability (`gate_weights`)

### 5. Explainability
- Grad-CAM for image modalities (US, X-Ray)
- Temporal attention for audio (CRNN)
- Linked to inference for audit trail

---

## Indexing Strategy

```sql
-- Primary lookups
CREATE INDEX idx_session_patient ON SCREENING_SESSION(patient_id);
CREATE INDEX idx_modality_session ON MODALITY(session_id);
CREATE INDEX idx_modality_type ON MODALITY(modality_type);
CREATE INDEX idx_embedding_modality ON EMBEDDING(modality_id);
CREATE INDEX idx_embedding_model ON EMBEDDING(model_id);

-- Label queries
CREATE INDEX idx_label_session ON DIAGNOSIS_LABEL(session_id);
CREATE INDEX idx_split_session ON DATA_SPLIT(session_id);
CREATE INDEX idx_split_name ON DATA_SPLIT(split_name);

-- Inference & monitoring
CREATE INDEX idx_inference_session ON INFERENCE_RESULT(session_id);
CREATE INDEX idx_inference_gmu ON INFERENCE_RESULT(gmu_id);
CREATE INDEX idx_inference_created ON INFERENCE_RESULT(created_at);
```

---

## Data Flow Summary

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   PATIENT   │────▶│ SCREENING_SESSION│────▶│  MODALITY   │
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
                    ┌──────────────┐                 │
                    │DIAGNOSIS_LABEL◀────────────────┘
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ AUDIO_REC  │  │ ULTRASOUND │  │  XRAY_STUDY│
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          ▼               ▼               ▼
    ┌─────────────────────────────────────────────┐
    │           SPECIALIST_MODEL (Phase-1)        │
    │  CRNN_Audio │ NTSNet_US │ EfficientNet_XRay │
    └────────────────────┬────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────┐
    │                  EMBEDDING                  │
    │          (512-dim per modality)             │
    └────────────────────┬────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────┐
    │                GMU_MODEL (Phase-2)          │
    │    Sigmoid Gates → Concat → MLP → Logit     │
    └────────────────────┬────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────┐
    │            INFERENCE_RESULT                 │
    │  probability_chd │ predicted_label │ gates  │
    └─────────────────────────────────────────────┘
```

---

## Normalization Notes

- **3NF compliant**: No transitive dependencies
- **Modality subtypes** use shared PK (1:1 with MODALITY)
- **EMBEDDING** stores vectors as BLOB/VECTOR; could be externalized to vector DB
- **JSON columns** used for variable schemas (gate weights, training config, defects)
- **Soft deletes** via `is_active` / `is_usable` flags instead of hard deletes

---

## Scalability Considerations

| Table | Expected Scale | Partitioning Strategy |
|-------|---------------|----------------------|
| PATIENT | ~10K-100K | None needed |
| SCREENING_SESSION | ~50K-500K | Partition by `session_date` (monthly) |
| MODALITY | ~150K-1.5M | Partition by `modality_type` + `session_date` |
| EMBEDDING | ~150K-1.5M | Partition by `model_id` + `extracted_at` |
| INFERENCE_RESULT | ~50K-500K | Partition by `created_at` (monthly) |
| TRAINING_RUN | ~1K-10K | None needed |

---

## Migration from Current CSV Format

Current CSVs (per-modality):
```
patient_id | us_path | label [+ fold, frame_idx]
patient_id | xray_path | label
patient_id | audio_path | label
```

Multimodal CSV:
```
patient_id | audio_path | us_path | xray_path | label
```

**Migration mapping:**
- `patient_id` → PATIENT.patient_id (create if not exists)
- Each row → SCREENING_SESSION (one per row)
- Non-NaN paths → MODALITY rows (type-specific subtype)
- `label` → DIAGNOSIS_LABEL (primary_diagnosis: CHD if 1 else NORMAL)
- `fold` → DATA_SPLIT.fold (if cross-validation used)