# 🌊 SeaDan Project

Software สำหรับการวิเคราะห์การกัดเซาะของชายหาด

---

## 📦 สิ่งที่ต้องมี

- [Miniconda](https://www.anaconda.com/download/success) (Python environment manager)
- [Git](https://git-scm.com/downloads) (version control)

---

## ⚙️ ขั้นตอนการติดตั้ง

### 1️⃣ ดาวน์โหลดโปรเจกต์

```bash
git clone https://github.com/suchayapanchuay/SeaDan_BlankSpace.git
cd SeaDan_BlankSpace
```

> **Windows Users:** สลับไปยัง branch ที่เหมาะสม:
```bash
git checkout windows
```

---

### 2️⃣ สร้าง Conda Environment
```bash
conda env create -f seadanenv.yml
conda activate seadanenv
```
---

## 📁 โครงสร้างโปรเจกต์

```plaintext
SeaDan_BlankSpace/
├── develop_space/
├── image/
├── SeaDan-Flow/              ← สำหรับ windows
├── .gitignore
├── environment_guide.md
├── open3d_requirements.txt
├── requirements.txt
├── seadanenv.yml             ← Conda Environment
├── visualize_color.py
├── visualize_volume.py
└── visualize.py
```

---
## ▶️ การรันโปรแกรม
### 🪟 สำหรับ Windows:
```bash
python .\SeaDan-Flow\SeaDanFlow_dev0.py
```

### 🍎 สำหรับ macOS / Linux:
```
python3 develop_space/demo8.py
```

---

## ❗ หมายเหตุ

- สำหรับ Windows: การใช้งานควรอยู่ใน branch `windows` และใช้โปรแกรม `SeaDanFlow_dev0.py` ที่อยู่ใน `SeaDan-Flow`
- หากพบปัญหา Open3D ในบางระบบให้ดูเพิ่มเติมใน `open3d_requirements.txt`

---

## 🤝 ผู้พัฒนา

พัฒนาโดย BlankSpace @ Thammasat University — Software Engineering
