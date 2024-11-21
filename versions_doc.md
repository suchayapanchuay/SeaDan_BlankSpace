## **legacy version จะถูกเก็บไว้อยู่ใน** `old_version`
- `pickfile_vis.py` เป็น version แรกที่เริ่มเป็นรูปเป็นร่าง version นี้จะมี feature คือ การเลือกไฟล์ผ่าน filedialog และ visualization
- `main_pick_step_vis.py` เป็น version ที่พัฒนาต่อจาก `pickfile_vis.py` โดยเพิ่มการปรับ step ในการ align ข้อมูล point cloud เพื่อรองรับ scale ของข้อมูลที่หลากหลาย
- `main_calculate_program.py` เป็น version ที่สามารถคำนวณปริมาตรที่เปลี่ยนแปลงได้แล้ว*โดย point cloud ทั้งสองชุดต้องถูก set latitude, longtitude, altitude มาก่อนหน้าแล้วเพื่อให้ point cloud ของทั้งสองช่วงเวลาอยู่ในพิกัดเดียวกัน*
- `SeaDan_alpha.py` เป็นเวอร์ชันล่าสุดที่สเถียรแล้วปัจจุบันเป็น version ที่พัฒนาต่อมาจาก `main_calculate_program.py` โดยมี feature เพิ่มเติมคือ ผู้ใช้สามารถทำการ visualization ข้อมูล point cloud ที่ละไฟล์ได้

## **latest version จะถูกเก็บไว้ใน** `standard_version`
- `main.py` เป็นโปรแกรมที่พัฒนาต่อมาจาก `SeaDan_alpha.py` โดยที่ version นี้มีการพัฒนา minor เล็ก เช่น software icon, plot altitude พร้อมกันในหน้าเดียว ซึ่งต่างจาก version ก่อนหน้าที่ average altitude plot ที่ละอย่าง(source, target, target-source) ซึ่งทำให้ผู้ใช้ดูและวิเคราะห์ข้อมูลได้ยาก

## **developing version (unstable version)** `develop_space`
- `main.py` minor changing