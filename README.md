# SMASH CBNU · 충북대 부수기

충북대학교 개신동 캠퍼스를 3D로 부수는 시험기간 스트레스 해소 게임입니다.
[SMASH KMU](https://hong-iron.github.io/SMASH-KMU/)(국민대 부수기)를 참고해 만들었습니다.

**플레이:** https://jjjjjjong.github.io/SMASH-CBNU/

## 도구

| 키 | 도구 | 설명 |
|---|---|---|
| 1 | 폭탄 | 클릭한 곳에 폭탄을 던져 넓게 날림 |
| 2 | 배트 | 클릭한 곳을 멀리 날림 (크기 3단계). 날아간 조각이 다른 건물도 부숨 |
| 3 | 레이저 | 왼쪽 드래그로 건물을 자름 |
| 4 | 운석 | 하늘에서 운석이 떨어짐 |
| 5 | 지진 | 클릭한 곳이 진앙 (규모 5·7·9) |
| 6 | 핵폭탄 | 캠퍼스 대부분이 사라짐 |

조작: 클릭 도구 사용 · 드래그 회전 · 우클릭 드래그 이동 · 휠 확대 · `Ctrl+Z` 되돌리기 · `N` 북쪽 · `H` 처음 시점 · `T` 위에서 보기

## 로컬 실행

`index.html`을 브라우저로 열면 됩니다 (three.js와 글꼴을 CDN에서 불러오므로 인터넷 연결 필요). 열리지 않으면 이 폴더에서:

```bash
python -m http.server 8765
```

후 http://localhost:8765 접속.

## 데이터 출처

- 건물·도로·녹지·나무: © [OpenStreetMap](https://www.openstreetmap.org/copyright) 기여자, [ODbL](https://opendatacommons.org/licenses/odbl/) 라이선스. `data.js`는 OSM 데이터를 가공한 파생 데이터베이스이며 ODbL을 따릅니다.
- 지형 고도: [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) (SRTM 기반)
- 건물 겉모습은 실제 사진이 아닌 일반 재질입니다.

충북대학교와 관계없는 비공식 팬 게임입니다.
