# -*- coding: utf-8 -*-
"""
[예제 2-4] 웹 캠에서 비디오 읽기            (교안 슬라이드 7)

웹캠에서 실시간으로 프레임을 읽어 화면에 표시합니다.
동영상 처리의 가장 기본이 되는 '읽기 → 표시 → 반복' 구조를 익힙니다.

▶ 실행 환경 : 로컬(VS Code 등) + 웹캠 필요. (Colab에서는 창 표시가 동작하지 않습니다.)
▶ 종료 방법 : 영상 창을 클릭해 활성화한 뒤 'q' 키를 누릅니다.

──────────────────────────────────────────────────────────────────
[화면이 검게만 나올 때 / 카메라가 안 켜질 때]
 이 예제는 아래 두 가지 문제를 자동으로 처리합니다.
 1) 백엔드(backend) 문제 : Windows에서 CAP_DSHOW가 검은 화면만 주는 카메라가 있습니다.
    → CAP_MSMF, 기본값 등 여러 백엔드를 순서대로 시도합니다.
 2) 웜업(warm-up) 문제 : 카메라가 켜진 직후 처음 몇 프레임은 검게 나옵니다.
    → 처음 몇 프레임을 버리고, 실제 영상이 들어오는지 확인합니다.

 그래도 안 되면 코드 문제가 아니라 'Windows 설정' 문제일 수 있습니다:
   설정 > 개인정보 보호 및 보안 > 카메라
   - '카메라 액세스' 켜기
   - '앱이 카메라에 액세스하도록 허용' 켜기
   - '데스크톱 앱이 카메라에 액세스하도록 허용' 켜기  (VS Code/파이썬은 여기에 해당)
 또한 Zoom/Teams/카메라 앱 등 다른 프로그램이 카메라를 쓰고 있으면 꺼주세요.
──────────────────────────────────────────────────────────────────
"""
import cv2 as cv
import sys


def open_camera():
    """여러 (카메라번호, 백엔드) 조합을 시도해, 실제로 '밝은' 프레임이 들어오는 카메라를 연다."""
    # 시도할 백엔드 목록 (이름, 백엔드 상수)
    backends = [
        ("MSMF (Media Foundation)", cv.CAP_MSMF),   # Windows 기본. 검은 화면일 때 1순위 대안
        ("DSHOW (DirectShow)",      cv.CAP_DSHOW),
        ("기본값(AUTO)",            cv.CAP_ANY),
    ]
    for cam_index in (0, 1, 2):                     # 내장캠이 0이 아닐 수도 있어 여러 번호 시도
        for name, backend in backends:
            cap = cv.VideoCapture(cam_index, backend)
            if not cap.isOpened():
                cap.release()
                continue

            # 웜업 : 처음 몇 프레임을 버리고(카메라 안정화), 밝기를 확인
            ok, frame = False, None
            for _ in range(15):
                ok, frame = cap.read()
                if ok and frame is not None and frame.mean() > 5:   # 평균 밝기 > 5 이면 정상 영상
                    break

            if ok and frame is not None and frame.mean() > 5:
                print(f"카메라 연결 성공 → index={cam_index}, backend={name}, 평균밝기={frame.mean():.1f}")
                return cap

            # 열리긴 했으나 검은 화면 → 다음 조합 시도
            print(f"  (검은 화면) index={cam_index}, backend={name} → 다음 조합 시도")
            cap.release()
    return None


cap = open_camera()
if cap is None:
    sys.exit("카메라 연결 실패: 위 주석의 'Windows 설정 > 카메라' 항목과 다른 앱의 카메라 점유를 확인하세요.")

while True:
    ret, frame = cap.read()                     # 한 프레임 읽기 (ret=성공여부, frame=영상 배열)

    if not ret:                                 # 프레임을 못 읽으면(카메라 끊김 등) 루프 종료
        print('프레임 획득에 실패하여 루프를 나갑니다.')
        break

    cv.imshow('Video display', frame)           # 창에 프레임 표시

    key = cv.waitKey(1)                          # 1밀리초 동안 키 입력 대기(화면 갱신도 이 안에서 일어남)
    if key == ord('q'):                          # 'q' 키가 들어오면 종료
        break

cap.release()                                   # 카메라 자원 반납 (반드시 호출!)
cv.destroyAllWindows()                          # 열린 모든 창 닫기
