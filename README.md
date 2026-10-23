# SMASH CBNU · 충북대 부수기

충북대학교 개신동 캠퍼스를 3D로 부수는 시험기간 스트레스 해소 게임입니다.
[SMASH KMU](https://hong-iron.github.io/SMASH-KMU/)(국민대 부수기)를 참고해 만들었습니다.

**플레이:** https://jjjjjjong.github.io/SMASH-CBNU/

## 도구

| 키 | 도구 | 설명 |
|---|---|---|
| 1 | 폭탄 | 클릭한 곳에 폭탄을 던져 넓게 날림 |
| 2 | 배트 | 거대한 배트로 휘둘러 날림 (크기 ×0.5~3). 날아가는 조각을 또 치면 공중 콤보, 70 m 넘게 날아가면 홈런 |
| 3 | 레이저 | 왼쪽 드래그로 건물을 자름 |
| 4 | 운석 | 하늘에서 운석이 떨어짐 |
| 5 | 지진 | 클릭한 곳이 진원. 규모 4~10, 땅이 물결치고 갈라지며 약한 층부터 무너짐 |
| 6 | 핵폭탄 | 캠퍼스 대부분이 사라짐 |

조작: 클릭 도구 사용 · 드래그 회전 · 우클릭 드래그 이동 · 휠 확대 · `Ctrl+Z` 되돌리기 · `N` 북쪽 · `H` 처음 시점 · `T` 위에서 보기

## 로컬 실행

이 폴더의 `run.bat`을 더블클릭하면 서버가 켜지고 브라우저에서 게임이 열립니다 (http://localhost:8770).
three.js와 글꼴을 CDN에서 불러오므로 인터넷 연결이 필요합니다.

직접 서버를 켤 때는 **이 폴더 안에서** 실행해야 합니다 (상위 폴더에서 켜면 폴더 목록만 보입니다):

```bash
python -m http.server 8770
```

## 데이터 출처

- 건물·도로·녹지·나무: © [OpenStreetMap](https://www.openstreetmap.org/copyright) 기여자, [ODbL](https://opendatacommons.org/licenses/odbl/) 라이선스. `data.js`는 OSM 데이터를 가공한 파생 데이터베이스이며 ODbL을 따릅니다.
- 지형 고도: [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) (SRTM 기반)
- 건물 겉모습은 실제 사진이 아닌 일반 재질입니다.

충북대학교와 관계없는 비공식 팬 게임입니다.
