# GitHub 공개 저장소 만들기 (초보자 안내)

1. **실제 프로젝트 코드인지 확인:** 이 ZIP의 코드는 논문을 바탕으로 재구성한 참고 코드입니다. 논문에서 직접 사용한 전체 원본 코드는 아닙니다. 학과가 '실제 프로젝트 코드 공개'를 요구한다면 팀원에게 원본 `.ino`, `.py`와 익명화된 데이터 파일을 받아 교체하세요.
2. GitHub 로그인 후 https://github.com/new 열기
3. 저장소 이름에 `robot-arm-ann-po-mppt` 입력
4. 공개 범위를 **Public**으로 선택한 후 **Create repository** 클릭
5. ZIP을 **압축 해제**하고 저장소 페이지의 **Add file → Upload files** 클릭
6. 압축 해제된 폴더 **안에 있는 파일과 폴더**(README.md, firmware, scripts, mppt_reference 등)를 선택하여 업로드하고 **Commit changes** 클릭
7. 저장소에 들어가서 **README.md**와 `scripts/`, `firmware/` 폴더가 정상 표시되는지 확인
8. 주소창의 저장소 URL을 복사해 학교 양식의 `프로젝트 코드가 공개된 Github Repository URL` 항목에 붙여넣기

예시 URL 형태: `https://github.com/본인계정/robot-arm-ann-po-mppt`

**이는 아직 존재하지 않는 예시 경로입니다.** 실제 저장소를 공개한 후에만 실제 URL이 생깁니다.

### 대체 업로드 방법

Git이 설치되어 있다면 폴더에서 아래 명령을 사용할 수 있습니다.

```bash
git init
git add .
git commit -m "Initial thesis-informed MPPT reference implementation"
git branch -M main
git remote add origin https://github.com/본인계정/robot-arm-ann-po-mppt.git
git push -u origin main
```

업로드 전 원본 측정자료 개인정보/학번, 비밀번호, 접근토큰, 팀원 공개 동의와 코드 검증 여부를 꼭 점검하세요.
