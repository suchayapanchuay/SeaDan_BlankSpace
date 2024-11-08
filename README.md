# Blankspace
repo นี้ประกอบไปด้วย
- code ซึ่งจะเก็บไว้ใน `standard_version` ซึ่งไว้เก็บ version หลักที่สเถียรซึ่งเพื่อให้ทุกคนสามารถมี version ที่ไว้นำไป พัฒนาต่อได้โดยทำต่อจาก version นี้
- code ที่เก็บไว้ใน `old_version` ไว้เก็บ code ของ version สเถียรที่ผ่านๆมา
- `develop_space` เป็น directory ที่เก็บ code ที่กำลังพัฒนาอยู่ ซึ่งพัฒนาต่อจาก version ใน     `standard_version`
- `environment_guide.md` เป็นไกด์ที่บอกวิธีการเตรียม environment สำหรับการรันและพัฒนา software ซึ่งจะบอกตั้งแต่ขั้นตอนการสร้าง virtual environment รวมถึงการ activate virtualenv หรือ virtualenvironment
- requirements
    - `open3d_requirements.txt` เป็นไฟล์ที่เก็บ package หรือ libary requirements ที่ open3d ต้องการ
    - `requirements.txt` เป็นไฟล์ที่เก็บ libary หรือ package ที่ project นี้ต้องการ
- ถ้าต้องการเก็บ *data set* ให้สร้าง folder ที่ชื่อว่า `dataset` เพื่อเก็บ data sets หรือ folder ย่อยที่ไว้เก็ฐ datasets