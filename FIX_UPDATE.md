## ⚠️ VẤN ĐỀ: End User Không Update Được App

### Triệu chứng
- User đang dùng app v1.0.0
- Khi click "Update Available!" → Download v1.2.2.exe
- Chạy file mới → Lỗi: `No module named 'pandas._libs.hashtable'`

### Nguyên nhân
File .exe được GitHub Actions build **VẪN THIẾU** pandas hidden imports dù spec file đã có.

### Giải pháp: Xóa tag v1.2.2 và tạo v1.2.3 mới

#### Bước 1: Xóa tag và release cũ
```bash
# Xóa tag local
git tag -d v1.2.2

# Xóa tag trên remote
git push origin :refs/tags/v1.2.2
```

Sau đó:
1. Vào: https://github.com/TrH203/Clinic-Auto-Fill/releases
2. Xóa release v1.2.2

#### Bước 2: Commit tất cả changes và tạo tag mới
```bash
# Add all files
git add .
git commit -m "v1.2.3: Complete fix with spec file and workflow"

# Update VERSION
echo "1.2.3" > VERSION
git add VERSION
git commit -m "Bump to v1.2.3"

# Create tag
git tag v1.2.3
git push origin main
git push origin v1.2.3
```

#### Bước 3: Đợi GitHub Actions build (~10 phút)
- Vào: https://github.com/TrH203/Clinic-Auto-Fill/actions
- Click vào workflow "Build and Release"
- Đợi chạy xong (màu xanh ✅)

#### Bước 4: Kiểm tra release
1. Vào: https://github.com/TrH203/Clinic-Auto-Fill/releases
2. Tìm release v1.2.3
3. Download file `ClinicAutoTool-v1.2.3.exe`
4. **Test trên máy Windows:**
   - Double click .exe
   - Xem có lỗi pandas không

#### Bước 5: Nếu vẫn lỗi → Build manual

Nếu GitHub Actions vẫn build thiếu imports, cần build manual trên Windows:

**On Windows machine:**
```cmd
pip install -r requirements.txt
pyinstaller ClinicAutoTool.spec
```

File output: `dist/ClinicAutoTool.exe`

Sau đó:
1. Test file .exe này trên Windows
2. Nếu chạy OK → Upload manual lên release v1.2.3

### Debug: Tại sao GitHub Actions build thiếu imports?

Có thể do:
1. ❌ PyInstaller trên Windows chưa install đủ dependencies
2. ❌ Spec file chưa được checkout đúng
3. ❌ Python version không khớp

### Solution tạm thời: Build và upload Manual

Nếu GitHub Actions không hoạt động:
1. Build trên máy Windows local
2. Upload .exe thủ công lên GitHub release
3. Hoặc disable GitHub Actions, chỉ upload manual

---

## 📝 Checklist Debug

- [ ] Xóa tag v1.2.2
- [ ] Xóa release v1.2.2  
- [ ] Commit all changes
- [ ] Tạo tag v1.2.3
- [ ] Đợi GitHub Actions build
- [ ] Download .exe và test trên Windows
- [ ] Nếu OK → End user có thể update
- [ ] Nếu lỗi → Build manual trên Windows
