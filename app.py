import streamlit as st
import pandas as pd
import yfinance as yf
import altair as alt
import re
from datetime import datetime, timedelta

# 1. 화면 설정
st.set_page_config(page_title="경제 지표 마스터 Pro (2026)", layout="wide")
st.title("📊 통합 경제 상황판 (2026 Final Fixed Ver.)")

# ==========================================
# [설정] 구글 스프레드시트 CSV 링크
# ==========================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdljkzb4qA58qS84TF8usbzb2NcUY8yHblkE6H_1TLleNvHbSG5se55MbbHU8mhAQ84gDk4nCSiq4v/pub?gid=0&single=true&output=csv"

# ==========================================
# [설정] 야후 파이낸스 자동 수집 리스트
# ==========================================
AUTO_TICKERS = {
    # 1. 환율
    "원/달러 환율": "KRW=X",        
    "달러 인덱스": "DX-Y.NYB",       
    "달러/유로": "USDEUR=X",        
    "달러/위안": "CNY=X",            
    "달러/엔": "JPY=X",
    "달러/루피": "INR=X",            
    
    # 2. 금리 (수기 관리)
    # "미국 국고채 10년물 금리": "^TNX",
    
    # 3. 원자재
    "유가 (WTI)": "CL=F",
    "천연가스 선물": "NG=F",
    "금 선물": "GC=F",
    "구리 선물": "HG=F",
    
    # 4. 주식
    "코스피 지수": "^KS11",
    "S&P 500": "^GSPC",
    "나스닥": "^IXIC",
    "다우 지수": "^DJI",            
    "니케이225": "^N225",
    "상해종합지수": "000001.SS",
    "유로스톡스 50 (유럽)": "^STOXX50E", 
    "인도(Nifty/Sensex)": "^NSEI",
    
    # 5. 심리/기타
    "VIX 지수 (공포지수)": "^VIX",
    "농산물 (S&P GSCI)": "^SPGSCI",

    # 6. 섹터/테마
    "🇺🇸 XLK (기술)": "XLK",
    "🇰🇷 TIGER Fn반도체TOP10": "396500.KS",
    "🇺🇸 XLY (경기소비재)": "XLY",
    "🇰🇷 KODEX 자동차": "091180.KS",
    "🇺🇸 XLC (커뮤니케이션)": "XLC",
    "🇰🇷 TIGER 미디어컨텐츠": "228810.KS",
    "🇺🇸 XLV (헬스케어)": "XLV",
    "🇰🇷 TIGER 헬스케어": "143860.KS",
    "🇺🇸 XLP (필수소비재)": "XLP",
    "🇰🇷 TIGER 200 필수소비재": "139230.KS",
    "🇺🇸 XLU (유틸리티)": "XLU",
    "🇰🇷 TIGER 200 유틸리티": "139270.KS", 
    "🇺🇸 XLF (금융)": "XLF",
    "🇰🇷 TIGER 은행": "091220.KS",
    "🇺🇸 XLE (에너지)": "XLE",
    "🇰🇷 TIGER 200 에너지화학": "139250.KS",
    "🇺🇸 XLI (산업재)": "XLI",
    "🇰🇷 TIGER 200 중공업": "139260.KS",
    "🇺🇸 XLB (소재)": "XLB",
    "🇰🇷 TIGER 200 철강소재": "139240.KS",
    "🇺🇸 XLRE (부동산)": "XLRE",
    "🇰🇷 TIGER 리츠부동산인프라": "329200.KS"
}

# ==========================================
# [설정] 지표별 상세 설명
# ==========================================
INDICATOR_DETAILS = {
    # ---------------- I. 금리 및 통화정책 지표 ----------------
    "한국 국고채 3년물": {
        "의미": "한국의 단기 금리(3년 만기 채권 수익률)", 
        "기준": "기준금리 + 0.3~0.5%p (정상 스프레드)",
        "높을 때": "경기 과열, 인플레 압력, 금리인상 기대", 
        "낮을 때": "경기 둔화, 완화적 통화정책 기대", 
        "시사점": "금리↑ → 채권 가격↓ / 성장주 약세 / 금융주 강세"
    },
    "한국 국고채 10년물": {
        "의미": "장기 금리, 미래 경기·인플레 기대 반영", 
        "기준": "3년물 금리보다 높아야 정상 (우상향)",
        "높을 때": "장기 경기 기대 상승, 인플레 기대↑", 
        "낮을 때": "장기 경기 둔화 우려", 
        "시사점": "장단기 스프레드(10-2년물)로 경기침체 여부 판단"
    },
    "한국 금리결정": {
        "의미": "한국은행이 결정하는 기준 정책금리", 
        "기준": "중립금리 (약 2.5% 내외 추정)",
        "높을 때": "물가억제 의지, 대출이자↑", 
        "낮을 때": "경기부양, 대출이자↓", 
        "시사점": "금리↑ → 소비·투자 위축 / 금리↓ → 주식·부동산↑"
    },
    "미국 국고채 2년물": {
        "의미": "단기금리, 연준 정책금리 전망 반영", 
        "기준": "미국 기준금리와 유사하게 움직임",
        "높을 때": "긴축기대↑ (금리인상 예상)", 
        "낮을 때": "완화기대↑ (금리인하 예상)", 
        "시사점": "연준의 향후 방향을 가장 민감하게 반영"
    },
    "미국 국고채 10년물": {
        "의미": "장기 경기·인플레 기대치 반영", 
        "기준": "4.0% (시장의 심리적 저항선)",
        "높을 때": "장기 성장 기대, 인플레 우려", 
        "낮을 때": "경기둔화, 안전자산 선호", 
        "시사점": "10년-2년 역전(역전 스프레드) → 경기침체 신호"
    },
    "연준 금리결정": {
        "의미": "미국의 기준금리 (FFR)", 
        "기준": "2.5~3.0% (장기 중립금리)",
        "높을 때": "긴축정책, 달러강세, 자산가격↓", 
        "낮을 때": "완화정책, 달러약세, 자산가격↑", 
        "시사점": "전세계 금융시장 방향의 핵심"
    },
    "중국 국고채 3년물": {
        "의미": "중국의 단기 경기·유동성 지표", 
        "기준": "2.0% 내외 (경기 부양 의지)",
        "높을 때": "긴축, 유동성 축소", 
        "낮을 때": "경기둔화, 경기부양 기대", 
        "시사점": "금리↓ = 부양 시그널"
    },
    "중국 국고채 10년물": {
        "의미": "장기 경기 기대", 
        "기준": "2.5% 내외",
        "높을 때": "장기 성장 기대", 
        "낮을 때": "장기 둔화 우려", 
        "시사점": "장기 금리 하락은 중국 경기 둔화 신호"
    },

    # ---------------- II. 실물경제 성장 지표 ----------------
    "한국 GDP": {
        "의미": "한국 경제의 성장률", 
        "기준": "2.0% (잠재성장률 수준)",
        "높을 때": "경기 확장, 소비·수출 활발", 
        "낮을 때": "경기둔화", 
        "시사점": "성장률 추세 확인용"
    },
    "미국 GDP": {
        "의미": "미국 경제의 성장률", 
        "기준": "1.8~2.0% (잠재성장률)",
        "높을 때": "경기호황", 
        "낮을 때": "경기침체 우려", 
        "시사점": "연준 긴축 지속 여부 판단"
    },
    "중국 GDP": {
        "의미": "중국 경기의 체력", 
        "기준": "4.5~5.0% (정부 목표치)",
        "높을 때": "수출·투자 활발", 
        "낮을 때": "내수 둔화, 수출 부진", 
        "시사점": "중국 관련 원자재·신흥국 주식에 영향"
    },

    # ---------------- III. 물가·고용 지표 ----------------
    "한국 CPI": {
        "의미": "소비자물가 상승률", 
        "기준": "2.0% (한은 물가안정 목표)",
        "높을 때": "인플레이션 압력, 금리인상 우려", 
        "낮을 때": "물가안정", 
        "시사점": "물가>2%면 긴축 가능성"
    },
    "미국 CPI": {
        "의미": "소비자물가 상승률", 
        "기준": "2.0% (연준 물가안정 목표)",
        "높을 때": "인플레 지속, 연준 긴축 유지", 
        "낮을 때": "물가안정, 완화 가능성↑", 
        "시사점": "시장은 CPI 발표에 매우 민감"
    },
    "미국 PPI": {
        "의미": "생산자물가 (도매단계)", 
        "기준": "CPI 선행지표 (통상 낮게 유지)",
        "높을 때": "비용상승, CPI 선행", 
        "낮을 때": "비용둔화", 
        "시사점": "생산자→소비자 전이 경로 체크"
    },
    "한국 PPI": {
        "의미": "한국 생산자물가", 
        "기준": "CPI 선행지표", 
        "높을 때": "제조업 비용 반영", 
        "낮을 때": "제조원가 압박", 
        "시사점": "CPI보다 1~2개월 선행"
    },
    "미국 고용지표(비농업 고용지수)": {
        "의미": "월별 고용증가 수 (NFP)", 
        "기준": "월 15~20만 명 증가 (적정)", 
        "높을 때": "경기확장, 임금상승, 인플레압력↑", 
        "낮을 때": "경기둔화, 실업 증가", 
        "시사점": "고용↑→연준 긴축 / 고용↓→완화 기대"
    },

    # ---------------- IV. 산업·경기 선행 지표 ----------------
    "ISM 제조업": {
        "의미": "제조업 경기 확장(>50) / 위축(<50)", 
        "기준": "50 (경기 확장/위축 분기점)", 
        "높을 때": "50↑ → 제조업 호황", 
        "낮을 때": "50↓ → 제조업 둔화", 
        "시사점": "경기선행지표로 신뢰도 높음"
    },
    "ISM 비제조업": {
        "의미": "서비스업 경기", 
        "기준": "50 (경기 확장/위축 분기점)", 
        "높을 때": "서비스 부문 호황", 
        "낮을 때": "서비스 부문 위축", 
        "시사점": "미국경제의 70% 비중 서비스업, 영향 큼"
    },
    "BDI": {
        "의미": "벌크 해운 운임 지수 (철광석, 석탄 등)", 
        "기준": "1,500 (호황/불황 심리적 경계)", 
        "높을 때": "원자재 수요↑, 글로벌 무역 호황", 
        "낮을 때": "무역둔화, 수요감소", 
        "시사점": "글로벌 경기 실물지표, 원자재시장 선행"
    },

    # ---------------- V. 위험·심리 및 원자재 ----------------
    "VIX 지수": {
        "의미": "S&P500 변동성 지수", 
        "기준": "20 (20 이하는 안정, 이상은 불안)", 
        "높을 때": "시장 불안, 주가 하락 위험", 
        "낮을 때": "안정, 위험자산 선호", 
        "시사점": "20↑ → 공포 / 15↓ → 낙관"
    },
    "유가 (WTI)": {
        "의미": "서부 텍사스산 원유", 
        "기준": "70~80불 (적정 유가)", 
        "높을 때": "인플레 유발, 비용↑", 
        "낮을 때": "경기 침체 시 수요↓", 
        "시사점": "에너지주 및 물가에 직접 영향"
    },
    "금 선물": {
        "의미": "안전자산", 
        "기준": "실질금리 및 달러가치와 역행", 
        "높을 때": "위험회피·인플레 방어 수요↑", 
        "낮을 때": "위험선호↑", 
        "시사점": "금↑ = 불확실성↑"
    },
    "구리 선물": {
        "의미": "경기민감 원자재", 
        "기준": "글로벌 제조업 경기와 동행", 
        "높을 때": "경기회복 기대", 
        "낮을 때": "경기둔화", 
        "시사점": "'Dr. Copper'라 불림 — 경기체감 지표"
    },
    "천연가스 선물": {
        "의미": "에너지 수급 불균형", 
        "기준": "계절적 요인(겨울) 중요", 
        "높을 때": "원가압박, 물가상승 위험", 
        "낮을 때": "에너지 수급 완화", 
        "시사점": "유럽·겨울철 민감"
    },
    "농산물": {
        "의미": "농산물 가격지수 (S&P GSCI)", 
        "기준": "애그플레이션 발생 여부", 
        "높을 때": "식품 인플레, 원자재비용↑", 
        "낮을 때": "물가 안정", 
        "시사점": "곡물·식품 관련주와 연동"
    },

    # ---------------- VI. 환율 및 통화 지표 ----------------
    "달러 인덱스": {
        "의미": "주요 6개국 통화 대비 달러 가치", 
        "기준": "100 포인트 (강/약 분기점)", 
        "높을 때": "달러 강세, 글로벌 유동성 축소", 
        "낮을 때": "달러 약세, 위험자산 선호", 
        "시사점": "달러가 꺾여야 신흥국 증시가 감"
    },
    "원/달러 환율": {
        "의미": "원화 대비 달러 가치 (1달러=?)", 
        "기준": "1,200~1,300원 (뉴노멀)", 
        "높을 때": "달러 강세 (외인 이탈)", 
        "낮을 때": "원화 강세 (자금 유입)", 
        "시사점": "수출주 유리 vs 수입물가 상승"
    },
    "달러/엔": {
        "의미": "엔화 대비 달러 가치 (1달러=?)", 
        "기준": "130~140엔 (엔저 경계)", 
        "높을 때": "엔저 (일본 수출 호조)", 
        "낮을 때": "엔고 (안전자산 선호)", 
        "시사점": "위기 시 엔화 강세 경향"
    },
    "달러/유로": { 
        "의미": "유로 대비 달러 가치 (1달러=?)", 
        "기준": "0.90~0.92 유로", 
        "높을 때": "달러 강세 (유로 약세)", 
        "낮을 때": "달러 약세 (유로 강세)", 
        "시사점": "ECB(유럽중앙은행) 통화정책 영향"
    },
    "달러/위안": {
        "의미": "위안화 대비 달러 가치 (1달러=?)", 
        "기준": "7.0~7.2 위안 (포치 경계선)", 
        "높을 때": "위안화 약세 (자본 유출)", 
        "낮을 때": "위안화 강세 (경기 회복)", 
        "시사점": "중국 경기 신뢰도 지표"
    },
    "달러/루피": { 
        "의미": "인도 루피화 가치 (1달러=?)", 
        "기준": "83~84 루피", 
        "높을 때": "루피화 약세 (수입 부담)", 
        "낮을 때": "루피화 강세 (성장 기대)", 
        "시사점": "신흥국 성장 척도 (인도)"
    },

    # ---------------- VII. 주가지수 ----------------
    "코스피 지수": {
        "의미": "한국 대형주 지수", 
        "기준": "PBR 1.0배 (저평가 기준)", 
        "높을 때": "경기회복, 수출호조", 
        "낮을 때": "경기둔화, 외인자금 유출", 
        "시사점": "원달러·반도체 사이클 영향 큼"
    },
    "S&P 500": {
        "의미": "미국 대형주 지수", 
        "기준": "역사적 우상향 추세선", 
        "높을 때": "미국 경기 자신감", 
        "낮을 때": "경기둔화, 기업실적 우려", 
        "시사점": "글로벌 벤치마크"
    },
    "나스닥": {
        "의미": "미국 기술주 중심", 
        "기준": "금리에 매우 민감", 
        "높을 때": "성장기대, 유동성↑", 
        "낮을 때": "금리상승기 약세", 
        "시사점": "금리 하락기 강세"
    },
    "상해종합지수": {
        "의미": "중국 증시", 
        "기준": "3,000 포인트 (심리적 지지선)", 
        "높을 때": "경기부양, 유동성↑", 
        "낮을 때": "부동산침체, 소비둔화", 
        "시사점": "중국 내수·정책 방향 반영"
    },
    "니케이": {
        "의미": "일본 증시", 
        "기준": "엔화 환율과 반대 방향", 
        "높을 때": "엔약세·수출호조", 
        "낮을 때": "엔강세·성장둔화", 
        "시사점": "달러/엔과 반비례 관계"
    },
    "인도": {
        "의미": "인도 증시", 
        "기준": "고성장 프리미엄 반영", 
        "높을 때": "신흥국 성장대표", 
        "낮을 때": "글로벌 긴축기 약세", 
        "시사점": "인프라·IT 성장주 중심"
    },
    "유로스톡스": {
        "의미": "유럽 50개 대표 기업", 
        "기준": "유럽 경기 회복 여부", 
        "높을 때": "유럽 경기 회복", 
        "낮을 때": "유로존 침체 우려", 
        "시사점": "글로벌 자산 배분의 한 축"
    },

    # ---------------- VIII. 섹터/테마 ----------------
    "🇺🇸 XLK (기술)": {
        "의미": "us XLK / KR Fn반도체TOP10",
        "특징": "[공격수] IT / 반도체",
        "기준": "금리 인하 & AI 투자",
        "높을 때": "금리 인하 기대, AI 붐",
        "낮을 때": "고금리, 경기 침체",
        "시사점": "애플, 엔비디아, 삼성전자 포함"
    },
    "🇰🇷 TIGER Fn반도체TOP10": {
        "의미": "us XLK / KR Fn반도체TOP10",
        "특징": "[공격수] IT / 반도체",
        "기준": "금리 인하 & AI 투자",
        "높을 때": "금리 인하 기대, AI 붐",
        "낮을 때": "고금리, 경기 침체",
        "시사점": "애플, 엔비디아, 삼성전자 포함"
    },
    "🇺🇸 XLY (경기소비재)": {
        "의미": "us XLY / KR 자동차/경기소비",
        "특징": "[공격수] 경기소비재",
        "기준": "소비심리지수 & 고용",
        "높을 때": "경기 호황, 지갑 열릴 때",
        "낮을 때": "경기 위축, 소비 감소",
        "시사점": "테슬라, 현대차 등. 경기에 민감함"
    },
    "🇰🇷 KODEX 자동차": {
        "의미": "us XLY / KR 자동차/경기소비",
        "특징": "[공격수] 경기소비재",
        "기준": "소비심리지수 & 고용",
        "높을 때": "경기 호황, 지갑 열릴 때",
        "낮을 때": "경기 위축, 소비 감소",
        "시사점": "테슬라, 현대차 등. 경기에 민감함"
    },
    "🇺🇸 XLC (커뮤니케이션)": {
        "의미": "us XLC / KR 미디어컨텐츠",
        "특징": "[공격수] 미디어/통신",
        "기준": "광고 경기 & 가입자",
        "높을 때": "플랫폼 성장, 광고 회복",
        "낮을 때": "규제 강화, 광고 둔화",
        "시사점": "구글, 메타, 네이버, 카카오 등"
    },
    "🇰🇷 TIGER 미디어컨텐츠": {
        "의미": "us XLC / KR 미디어컨텐츠",
        "특징": "[공격수] 미디어/통신",
        "기준": "광고 경기 & 가입자",
        "높을 때": "플랫폼 성장, 광고 회복",
        "낮을 때": "규제 강화, 광고 둔화",
        "시사점": "구글, 메타, 네이버, 카카오 등"
    },
    "🇺🇸 XLV (헬스케어)": {
        "의미": "us XLV / KR 헬스케어",
        "특징": "[수비수] 헬스케어",
        "기준": "고령화 & 임상 결과",
        "높을 때": "경기 방어 수요, 금리 인하",
        "낮을 때": "약가 인하 규제 이슈",
        "시사점": "고령화 수혜, 경기 무관 성장"
    },
    "🇰🇷 TIGER 헬스케어": {
        "의미": "us XLV / KR 헬스케어",
        "특징": "[수비수] 헬스케어",
        "기준": "고령화 & 임상 결과",
        "높을 때": "경기 방어 수요, 금리 인하",
        "낮을 때": "약가 인하 규제 이슈",
        "시사점": "고령화 수혜, 경기 무관 성장"
    },
    "🇺🇸 XLP (필수소비재)": {
        "의미": "us XLP / KR 필수소비재",
        "특징": "[수비수] 필수소비재",
        "기준": "가격 전가력 (물가)",
        "높을 때": "폭락장 방어, 가격 인상",
        "낮을 때": "위험자산 선호 심리",
        "시사점": "콜라, 라면, 담배 (없으면 안 됨)"
    },
    "🇰🇷 TIGER 200 필수소비재": {
        "의미": "us XLP / KR 필수소비재",
        "특징": "[수비수] 필수소비재",
        "기준": "가격 전가력 (물가)",
        "높을 때": "폭락장 방어, 가격 인상",
        "낮을 때": "위험자산 선호 심리",
        "시사점": "콜라, 라면, 담배 (없으면 안 됨)"
    },
    "🇺🇸 XLU (유틸리티)": {
        "의미": "us XLU / KR 유틸리티",
        "특징": "[수비수] 유틸리티",
        "기준": "국채 금리 (배당 매력)",
        "높을 때": "경기 침체 방어, 저금리",
        "낮을 때": "금리 급등 시 매력 감소",
        "시사점": "거래량 적음 주의. 전기/가스/수도 등 배당주 성격"
    },
    "🇰🇷 TIGER 200 유틸리티": {
        "의미": "us XLU / KR 유틸리티",
        "특징": "[수비수] 유틸리티",
        "기준": "국채 금리 (배당 매력)",
        "높을 때": "경기 침체 방어, 저금리",
        "낮을 때": "금리 급등 시 매력 감소",
        "시사점": "거래량 적음 주의. 전기/가스/수도 등 배당주 성격"
    },
    "🇺🇸 XLF (금융)": {
        "의미": "us XLF / KR 은행/증권",
        "특징": "[중간] 금융",
        "기준": "기준금리 & 예대마진",
        "높을 때": "적당한 고금리, 경기 견조",
        "낮을 때": "초저금리, 금융 위기",
        "시사점": "금리가 적당히 높을 때 좋음 (배당)"
    },
    "🇰🇷 TIGER 은행": {
        "의미": "us XLF / KR 은행/증권",
        "특징": "[중간] 금융",
        "기준": "기준금리 & 예대마진",
        "높을 때": "적당한 고금리, 경기 견조",
        "낮을 때": "초저금리, 금융 위기",
        "시사점": "금리가 적당히 높을 때 좋음 (배당)"
    },
    "🇺🇸 XLE (에너지)": {
        "의미": "us XLE / KR 에너지화학",
        "특징": "[경기민감] 에너지",
        "기준": "국제 유가 (WTI)",
        "높을 때": "유가 상승, 인플레이션",
        "낮을 때": "유가 급락, 수요 둔화",
        "시사점": "엑손모빌, S-Oil. 유가와 정비례"
    },
    "🇰🇷 TIGER 200 에너지화학": {
        "의미": "us XLE / KR 에너지화학",
        "특징": "[경기민감] 에너지",
        "기준": "국제 유가 (WTI)",
        "높을 때": "유가 상승, 인플레이션",
        "낮을 때": "유가 급락, 수요 둔화",
        "시사점": "엑손모빌, S-Oil. 유가와 정비례"
    },
    "🇺🇸 XLI (산업재)": {
        "의미": "us XLI / KR 중공업/기계",
        "특징": "[경기민감] 산업재/중공업",
        "기준": "설비투자 (CAPEX)",
        "높을 때": "공장 가동↑, 인프라 투자",
        "낮을 때": "투자 위축, 경기 둔화",
        "시사점": "방산, 항공, 건설기계. 공장 돌릴 때"
    },
    "🇰🇷 TIGER 200 중공업": {
        "의미": "us XLI / KR 중공업/기계",
        "특징": "[경기민감] 산업재/중공업",
        "기준": "설비투자 (CAPEX)",
        "높을 때": "공장 가동↑, 인프라 투자",
        "낮을 때": "투자 위축, 경기 둔화",
        "시사점": "방산, 항공, 건설기계. 공장 돌릴 때"
    },
    "🇺🇸 XLB (소재)": {
        "의미": "us XLB / KR 철강소재",
        "특징": "[경기민감] 소재/철강",
        "기준": "원자재 가격 & 중국",
        "높을 때": "원자재가 상승, 중국 부양",
        "낮을 때": "원자재가 하락, 디플레",
        "시사점": "포스코 등. 원자재 가격 따라감"
    },
    "🇰🇷 TIGER 200 철강소재": {
        "의미": "us XLB / KR 철강소재",
        "특징": "[경기민감] 소재/철강",
        "기준": "원자재 가격 & 중국",
        "높을 때": "원자재가 상승, 중국 부양",
        "낮을 때": "원자재가 하락, 디플레",
        "시사점": "포스코 등. 원자재 가격 따라감"
    },
    "🇺🇸 XLRE (부동산)": {
        "의미": "us XLRE / KR 부동산인프라",
        "특징": "[배당형] 부동산/리츠",
        "기준": "금리 (조달비용)",
        "높을 때": "금리 인하 시 최대 수혜",
        "낮을 때": "고금리, PF 부실 우려",
        "시사점": "건물 월세 받는 리츠. 금리 인하 시 꿀"
    },
    "🇰🇷 TIGER 리츠부동산인프라": {
        "의미": "us XLRE / KR 부동산인프라",
        "특징": "[배당형] 부동산/리츠",
        "기준": "금리 (조달비용)",
        "높을 때": "금리 인하 시 최대 수혜",
        "낮을 때": "고금리, PF 부실 우려",
        "시사점": "건물 월세 받는 리츠. 금리 인하 시 꿀"
    },
    
    # ==========================================================
    # 퀀트 전문가 시점 - 커스텀 버핏 지수 및 심리 지표 상세 설명
    # ==========================================================
    "CNN 공포/탐욕 지수": {
        "의미": "시장 참여자들의 감정 상태를 0(극단적 공포)에서 100(극단적 탐욕)으로 나타낸 지수",
        "기준": "50 (중립)",
        "높을 때": "75 이상 극단적 탐욕 (주식 시장 단기 고점, 매도 경계)",
        "낮을 때": "25 이하 극단적 공포 (주식 시장 단기 저점, 매수 기회)",
        "시사점": "워런 버핏의 격언 '남들이 탐욕스러울 때 공포를 느끼고, 공포를 느낄 때 탐욕스러워져라'를 수치화한 강력한 역발상 투자 지표."
    },
    "코스피 버핏 지수": {
        "의미": "한국 명목 GDP 대비 코스피 지수 비율 (거시적 거품 판독기)",
        "기준": "역사적 평균치 밴드 (통상 0.8 ~ 1.0 수준)",
        "높을 때": "실물 경제 대비 증시 과열 (거품 경고, 현금 비중 확대 고려)",
        "낮을 때": "실물 체력 대비 주식 시장 극심한 저평가 (강력한 매수 기회)",
        "시사점": "퀀트 관점에서 '코리아 디스카운트'를 감안해도 밴드 상단 돌파 시 리스크 관리 필수."
    },
    "S&P 500 버핏 지수": {
        "의미": "미국 명목 GDP 대비 S&P 500 비율 (미국 대형주 밸류에이션 척도)",
        "기준": "과거 10년 평균 추세선 (약 1.5 ~ 1.7 부근)",
        "높을 때": "매크로 펀더멘털을 초과한 밸류에이션 팽창 (조정 임박 신호)",
        "낮을 때": "거시 경제 대비 대형주 저평가 구간 (장기 투자 진입 적기)",
        "시사점": "연준 유동성 장세에선 기준이 높아지나, 역사적 상단 이탈 시 하락 다이버전스 주의."
    },
    "나스닥 버핏 지수": {
        "의미": "미국 명목 GDP 대비 나스닥 지수 비율 (기술주 버블 강도 측정)",
        "기준": "닷컴 버블 및 펜데믹 유동성 고점 대비 상대 비율",
        "높을 때": "AI 등 특정 테마에 의한 과도한 프리미엄 부여 (숏 헤지 고려 구간)",
        "낮을 때": "혁신 기술주의 펀더멘털 대비 과매도 (레버리지 진입 기회)",
        "시사점": "가장 변동성이 크며, 유동성 장세에서 가장 먼저 과열을 알리는 선행 지표."
    },
    "다우 버핏 지수": {
        "의미": "미국 명목 GDP 대비 다우 지수 비율 (전통 가치주/산업재 펀더멘털 평가)",
        "기준": "S&P 500 대비 상대적 안정성 및 역사적 평균 밴드",
        "높을 때": "전통 산업마저 과열된 전형적인 증시 상투 (현금화 강력 권고)",
        "낮을 때": "전통 우량주의 절대적 저평가 (방어 포트폴리오 구축 적기)",
        "시사점": "기술주 랠리 소외 시기엔 낮게 유지되나, 다우마저 고평가라면 시장 전체의 붕괴 리스크 내포."
    },
    "미국 통합 버핏 지수": {
        "의미": "미국 3대 지수(S&P, 나스닥, 다우) 합산을 GDP로 나눈 궁극의 월가 거품 판독기",
        "기준": "워런 버핏의 원본 지표(시총/GDP)를 3대 지수로 대리한 합성 척도",
        "높을 때": "'버핏이 현금을 쌓는 시기'. 주식 비중 축소 및 무위험 자산 확대 필수",
        "낮을 때": "'피가 낭자할 때 매수하라'. 패닉 셀링으로 인한 주식 풀(Full) 베팅 구간",
        "시사점": "개별 지수의 착시를 제거하고, 미국 증시 전체의 체급 대비 거품을 냉정하게 진단하는 핵심 지표."
    },
    "중국 버핏 지수": {
        "의미": "중국 명목 GDP 대비 상해종합지수 비율",
        "기준": "중국 정부의 부양책 및 거시 경제 체력 지표",
        "높을 때": "단기 유동성 과잉, 규제 리스크 부각 전",
        "낮을 때": "부동산 침체 및 내수 부진 선반영 (바닥권 확인 필요)",
        "시사점": "공산당의 정책 방향성(공동부유 등)에 따라 밴드 자체가 크게 요동침."
    },
    "일본 버핏 지수": {
        "의미": "일본 명목 GDP 대비 니케이 225 비율",
        "기준": "잃어버린 30년 탈출 및 엔저 수혜 여부 판단",
        "높을 때": "엔저 한계 도달 및 BOJ(일본은행) 금리 인상 경계",
        "낮을 때": "기업 지배구조 개선 및 디플레 탈출 사이클 초입",
        "시사점": "워런 버핏의 일본 상사 투자 이유를 증명하는 매크로 지표."
    }
}
DEFAULT_INFO = {"의미": "-", "기준": "-", "높을 때": "-", "낮을 때": "-", "시사점": "-"}

# 2. 데이터 로드 (1순위: 구글 시트 / 2순위: 로컬 엑셀 폴백)
@st.cache_data(ttl=600)
def load_files():
    df_macro = pd.DataFrame()     
    df_events_merged = pd.DataFrame() 
    google_sheet_success = False

    # [플랜 A] 1. 먼저 구글 스프레드시트(CSV) 로드를 시도합니다.
    try:
        df_raw = pd.read_csv(SHEET_CSV_URL)
        df_raw.columns = df_raw.columns.str.strip()

        if '날짜' not in df_raw.columns:
            for col in df_raw.columns:
                if str(col).lower() in ['date', '날짜']:
                    df_raw.rename(columns={col: '날짜'}, inplace=True)
                    break
        if '날짜' not in df_raw.columns:
             df_raw.rename(columns={df_raw.columns[0]: '날짜'}, inplace=True)

        for col in df_raw.columns:
            if col in ['내용', '비고', '이벤트', 'Event', 'Note', '코멘트']:
                temp = df_raw[['날짜', col]].copy()
                temp.rename(columns={col: '내용'}, inplace=True)
                temp.dropna(subset=['내용'], inplace=True)
                temp['날짜'] = pd.to_datetime(temp['날짜'], errors='coerce')
                df_events_merged = pd.concat([df_events_merged, temp])
                df_raw.drop(columns=[col], inplace=True)

        df_raw['날짜'] = pd.to_datetime(df_raw['날짜'], errors='coerce')
        df_raw.dropna(subset=['날짜'], inplace=True)
        df_raw['날짜'] = df_raw['날짜'].dt.normalize()
        
        df_macro = df_raw.groupby('날짜').last()
        google_sheet_success = True

    except Exception:
        pass # 구글 시트 실패 시 조용히 넘어감

    # [플랜 B] 2. 구글 시트 로드 실패 시, 로컬 macro.xlsx 파일 로드를 시도합니다.
    if not google_sheet_success:
        try:
            df_raw = pd.read_excel("macro.xlsx", sheet_name=0, header=None)
            header_row = -1
            for i in range(10):
                if df_raw.iloc[i].astype(str).str.contains("날짜|Date|date", case=False, na=False).any():
                    header_row = i
                    break
            
            if header_row != -1:
                df_raw = pd.read_excel("macro.xlsx", sheet_name=0, header=header_row)
            else:
                df_raw = pd.read_excel("macro.xlsx", sheet_name=0, header=0)
                df_raw.rename(columns={df_raw.columns[0]: '날짜'}, inplace=True)

            df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
            df_raw.columns = df_raw.columns.str.strip()

            if '날짜' not in df_raw.columns:
                for col in df_raw.columns:
                    if str(col).lower() in ['date', '날짜']:
                        df_raw.rename(columns={col: '날짜'}, inplace=True)
                        break
            if '날짜' not in df_raw.columns:
                 df_raw.rename(columns={df_raw.columns[0]: '날짜'}, inplace=True)

            for col in df_raw.columns:
                if col in ['내용', '비고', '이벤트', 'Event', 'Note', '코멘트']:
                    temp = df_raw[['날짜', col]].copy()
                    temp.rename(columns={col: '내용'}, inplace=True)
                    temp.dropna(subset=['내용'], inplace=True)
                    temp['날짜'] = pd.to_datetime(temp['날짜'], errors='coerce')
                    df_events_merged = pd.concat([df_events_merged, temp])
                    df_raw.drop(columns=[col], inplace=True)

            df_raw['날짜'] = pd.to_datetime(df_raw['날짜'], errors='coerce')
            df_raw.dropna(subset=['날짜'], inplace=True)
            df_raw['날짜'] = df_raw['날짜'].dt.normalize()
            
            df_macro = df_raw.groupby('날짜').last()

        except Exception:
            pass

        try:
            xls = pd.ExcelFile("macro.xlsx")
            for sheet in xls.sheet_names:
                if "이벤트" in sheet or "Event" in sheet:
                    df_sheet = pd.read_excel("macro.xlsx", sheet_name=sheet)
                    df_sheet.columns = df_sheet.columns.str.strip()
                    if '날짜' in df_sheet.columns and '내용' in df_sheet.columns:
                        df_sheet['날짜'] = pd.to_datetime(df_sheet['날짜'], errors='coerce')
                        df_sheet.dropna(subset=['날짜'], inplace=True)
                        df_sheet['날짜'] = df_sheet['날짜'].dt.normalize()
                        df_events_merged = pd.concat([df_events_merged, df_sheet])
        except:
            pass

    if not df_events_merged.empty:
        df_events_merged = df_events_merged.sort_values('날짜')

    # 현재 어떤 방식으로 데이터를 가져왔는지 Streamlit 세션 스테이트에 임시 저장 (알림용)
    if 'data_source' not in st.session_state:
        st.session_state['data_source'] = 'Google Sheet' if google_sheet_success else 'Local Excel'
    else:
        st.session_state['data_source'] = 'Google Sheet' if google_sheet_success else 'Local Excel'

    return df_macro, df_events_merged

# 3. 데이터 통합 (실시간 일간 업데이트 + ffill + 버핏 지수)
@st.cache_data
def get_combined_data(df_macro, df_events):
    df_auto = pd.DataFrame()
    start_date = (datetime.now() - timedelta(days=365*4)).strftime('%Y-%m-%d')
    
    for name, ticker in AUTO_TICKERS.items():
        try:
            # interval="1mo" 삭제 -> 실시간 Daily 데이터 수집
            data = yf.Ticker(ticker).history(start=start_date)
            if not data.empty:
                data.index = data.index.tz_localize(None)
                data.index = data.index.normalize() # 정확한 일자 매칭
                temp = data[['Close']].rename(columns={'Close': name})
                if ticker in ["^TNX", "^IRX"]: temp[name] = temp[name]
                if df_auto.empty: df_auto = temp
                else: df_auto = df_auto.join(temp, how='outer')
        except: continue

    if not df_macro.empty:
        final_df = df_macro.combine_first(df_auto)
    else:
        final_df = df_auto

    if final_df.empty: return final_df

    three_years_ago = datetime.now() - timedelta(days=365*3)
    final_df = final_df[final_df.index >= three_years_ago]
    
    # [핵심] 빈칸은 가장 최근 과거 값으로 자동 채워줍니다 (평행선 연장)
    final_df = final_df.sort_index(ascending=True).ffill().sort_index(ascending=False)
    
    cols_to_keep = []
    for c in final_df.columns:
        if "Unnamed" not in str(c):
            cols_to_keep.append(c)
    final_df = final_df[cols_to_keep]

    if not df_events.empty:
        events_for_join = df_events.copy()
        events_for_join.set_index('날짜', inplace=True)
        events_for_join['내용'] = events_for_join['내용'].astype(str)
        events_for_join = events_for_join.groupby(events_for_join.index)['내용'].apply(lambda x: ', '.join(x)).to_frame()
        events_for_join.rename(columns={'내용': '📝비고'}, inplace=True)
        final_df = final_df.join(events_for_join, how='left')
        cols = list(final_df.columns)
        if '📝비고' in cols:
            cols.insert(0, cols.pop(cols.index('📝비고')))
            final_df = final_df[cols]

    # ==========================================================
    # 커스텀 버핏 지수 계산 로직
    # ==========================================================
    if '한국 GDP' in final_df.columns and '코스피 지수' in final_df.columns:
        final_df['코스피 버핏 지수'] = final_df['코스피 지수'] / final_df['한국 GDP']
        
    if '미국 GDP' in final_df.columns:
        if 'S&P 500' in final_df.columns:
            final_df['S&P 500 버핏 지수'] = final_df['S&P 500'] / final_df['미국 GDP']
        if '나스닥' in final_df.columns:
            final_df['나스닥 버핏 지수'] = final_df['나스닥'] / final_df['미국 GDP']
        if '다우 지수' in final_df.columns:
            final_df['다우 버핏 지수'] = final_df['다우 지수'] / final_df['미국 GDP']
            
        if all(c in final_df.columns for c in ['S&P 500', '나스닥', '다우 지수']):
            final_df['미국 통합 버핏 지수'] = (final_df['S&P 500'] + final_df['나스닥'] + final_df['다우 지수']) / final_df['미국 GDP']

    if '중국 GDP' in final_df.columns and '상해종합지수' in final_df.columns:
        final_df['중국 버핏 지수'] = final_df['상해종합지수'] / final_df['중국 GDP']
        
    if '일본 GDP' in final_df.columns and '니케이225' in final_df.columns:
        final_df['일본 버핏 지수'] = final_df['니케이225'] / final_df['일본 GDP']
    # ==========================================================

    final_df.index.name = "날짜"
    return final_df

def categorize_columns(columns):
    categories = {
        "💰 1. 금리 및 통화정책": [],
        "📈 2. 실물경제 (성장/물가/산업)": [],
        "💱 3. 환율 및 원자재": [],
        "🏢 4. 주가지수 및 심리(VIX)": [],
        "💎 5. 섹터/테마": []
    }
    for col in columns:
        if col == "📝비고": continue
        name = str(col).lower()
        clean = re.sub(r'[\s/().,]', '', name)
        
        # 버핏 지수는 4번, 5번 양쪽 카테고리에 모두 추가
        if "버핏" in clean:
            categories["🏢 4. 주가지수 및 심리(VIX)"].append(col)
            categories["💎 5. 섹터/테마"].append(col)
            continue 
        
        if any(x in clean for x in ["금리", "국채", "국고채", "채권", "fed", "rate", "yield", "bond", "3년", "10년", "2년"]): 
            categories["💰 1. 금리 및 통화정책"].append(col)
        elif any(x in clean for x in ["xlk", "xly", "xlc", "xlv", "xlp", "xlu", "xlf", "xle", "xli", "xlb", "xlre", "tiger", "kodex", "kbstar"]):
            categories["💎 5. 섹터/테마"].append(col)
        # cnn, 탐욕 키워드를 4번에 추가
        elif any(x in clean for x in ["코스피", "s&p", "나스닥", "다우", "상해", "니케이", "인도", "주식", "스톡스", "니프티", "vix", "공포", "cnn", "탐욕"]): 
            categories["🏢 4. 주가지수 및 심리(VIX)"].append(col)
        elif any(x in clean for x in ["환율", "달러", "유로", "위안", "엔", "루피", "krw", "usd", "유가", "가스", "구리", "금", "은", "농산물", "oil", "gold"]):
            categories["💱 3. 환율 및 원자재"].append(col)
        elif any(x in clean for x in ["gdp", "cpi", "ppi", "고용", "pmi", "ism", "bdi", "성장", "물가"]):
            categories["📈 2. 실물경제 (성장/물가/산업)"].append(col)
            
    return categories

def get_indicator_detail(item_name):
    clean_name = re.sub(r'[\s/().,]', '', str(item_name)).lower()
    for key, val in INDICATOR_DETAILS.items():
        if re.sub(r'[\s/().,]', '', key).lower() in clean_name:
            return val
    return DEFAULT_INFO

# 5. 실행
df_macro, df_events = load_files()

if st.button("🔄 구글 시트 새로고침"):
    st.cache_data.clear()
    st.rerun()

df_final = get_combined_data(df_macro, df_events)

# ==========================================
# [데이터 진단기]
# ==========================================
with st.expander("🛠️ 데이터 진단 (구글 시트 연동 상태)", expanded=False):
    if df_macro.empty:
        st.error("❌ 구글 시트 데이터를 읽지 못했습니다. 링크 권한이나 열(날짜)을 확인해주세요.")
    else:
        st.success(f"✅ 구글 시트 로드 성공! (총 {len(df_macro)}개 행)")
        st.dataframe(df_macro.head(3))

if not df_final.empty:
    
    # ----------------------------------------------------
    # [1] 맨 위: 🏆 나만의 통합 차트 만들기
    # ----------------------------------------------------
    st.markdown("### 🏆 나만의 통합 차트 만들기 (Master Chart)")
    st.info("💡 원하는 지표를 골라 한 차트에서 흐름을 비교해보세요.")
    
    all_cols = [c for c in df_final.columns if c != '📝비고']
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        selected_master = st.multiselect("👇 지표 추가하기:", all_cols, default=all_cols[:2] if len(all_cols)>=2 else all_cols)
    with col_opt2:
        st.write("🔢 **옵션 설정**")
        scale_master = st.checkbox("📈 모양(추세)만 비교하기 (0~10 스케일 자동 변환)", value=True)
        show_labels_master = st.checkbox("차트에 값 표시하기", value=True)
        show_all_labels_master = st.checkbox("모든 점 표시 (통합 차트)", value=False, disabled=not show_labels_master)

    if selected_master:
        chart_data = df_final[selected_master].copy().sort_index(ascending=True).reset_index()
        melted = chart_data.melt('날짜', var_name='항목', value_name='실제값')
        
        def expand_info(item): return pd.Series(get_indicator_detail(item))
        info_df = melted['항목'].apply(expand_info)
        melted = pd.concat([melted, info_df], axis=1)

        def get_val_master(row):
            if scale_master:
                min_v = df_final[row['항목']].min()
                max_v = df_final[row['항목']].max()
                if min_v == max_v: return 0
                return (row['실제값'] - min_v) / (max_v - min_v) * 10
            return row['실제값']
        
        melted['표시값'] = melted.apply(get_val_master, axis=1)

        base = alt.Chart(melted).encode(x=alt.X('날짜:T', title='', axis=alt.Axis(format='%y/%m/%d', labelAngle=0)))
        
        lines = base.mark_line(point=True).encode(
            y=alt.Y('표시값', title=''),
            color=alt.Color('항목', legend=alt.Legend(orient='top', title=None)),
            tooltip=[
                alt.Tooltip('날짜', title='📅 날짜', format='%y/%m/%d'),
                alt.Tooltip('항목', title='📊 항목'),
                alt.Tooltip('실제값', title='💰 값', format=','),
                alt.Tooltip('기준:N', title='📏 기준'),
                alt.Tooltip('의미:N', title='🔹 의미'),
                alt.Tooltip('높을 때:N', title='🔺 높을때'),
                alt.Tooltip('낮을 때:N', title='🔻 낮을때'),
                alt.Tooltip('특징:N', title='✨ 특징'),
                alt.Tooltip('시사점:N', title='💡 시사점')
            ]
        )
        final_master_chart = lines

        if show_labels_master:
            text_data = melted if show_all_labels_master else melted[melted['날짜'] == melted.groupby('항목')['날짜'].transform('max')]
            labels = alt.Chart(text_data).mark_text(align='left', dx=8, dy=-8, fontSize=11, fontWeight='bold').encode(
                x='날짜:T', y='표시값', text=alt.Text('실제값', format=',.2f'), color=alt.value('black')
            )
            final_master_chart = final_master_chart + labels

        st.altair_chart(final_master_chart.properties(height=450).interactive(), use_container_width=True)
    
    st.markdown("---")

    # ----------------------------------------------------
    # [2] 중간: 5개 분야별 상세 보기
    # ----------------------------------------------------
    cats = categorize_columns(df_final.columns)
    
    with st.expander("🧭 지표 해석 가이드 (클릭)", expanded=False):
        st.markdown("""
        * **1. 금리**: 돈의 가격. (금리↑ = 주가↓, 채권↓)
        * **2. 경제**: GDP(성장), CPI(물가), PMI(심리). 50 이상이면 호황.
        * **3. 환율/원자재**: 달러/유가 강세는 한국 증시에 부담.
        * **4. 주식/심리**: 공포지수(VIX) 20 이하는 안정 구간.
        * **5. 섹터**: 금리 인하기엔 성장주(기술/바이오), 상승기엔 가치주(금융/에너지).
        """)

    all_cat = list(cats.keys())
    selected_cats = st.multiselect("👇 상세 분석할 분야 선택:", all_cat, default=all_cat)
    st.markdown("---")

    if selected_cats:
        layout = st.columns(2)
        for i, cat_name in enumerate(selected_cats):
            cols_in_cat = cats[cat_name]
            with layout[i % 2]:
                st.subheader(f"{cat_name}")
                if not cols_in_cat:
                    st.info("데이터 없음")
                    continue

                selected = st.multiselect(f"비교할 항목", cols_in_cat, default=cols_in_cat[:min(3, len(cols_in_cat))], key=f"sel_{cat_name}")
                if selected:
                    with st.expander("🎨 차트 스타일 설정", expanded=False):
                        custom_colors = {}
                        custom_dashes = {}
                        for idx, item in enumerate(selected):
                            c1, c2, c3 = st.columns([2, 1, 1])
                            with c1: st.write(f"**{item}**")
                            with c2:
                                default_colors = ['#000000', '#0000FF', '#FF0000', '#008000', '#800080', '#FFA500']
                                picked_color = st.color_picker(f"색상", default_colors[idx % 6], key=f"col_{cat_name}_{idx}")
                            with c3:
                                picked_style = st.selectbox(f"모양", ["실선", "점선", "대시"], key=f"sty_{cat_name}_{idx}")
                            custom_colors[item] = picked_color
                            if picked_style == "실선": custom_dashes[item] = [1, 0]
                            elif picked_style == "점선": custom_dashes[item] = [2, 2]
                            else: custom_dashes[item] = [5, 5]
                    
                    col_opts = st.columns(2)
                    with col_opts[0]:
                        suggestions = [c for c in selected if df_final[c].dtype != 'object' and df_final[c].mean() > 20]
                        scaled = st.multiselect("👇 0~10 스케일 변환", selected, default=suggestions, key=f"sc_{cat_name}")
                    with col_opts[1]:
                        st.write("🔢 **설정**")
                        show_labels = st.checkbox("값 표시", value=True, key=f"lbl_{cat_name}")
                        show_all_labels = st.checkbox("모든 점 표시", value=False, disabled=not show_labels, key=f"lbl_all_{cat_name}")

                    # 차트 데이터
                    chart_data = df_final[selected].copy().sort_index(ascending=True).reset_index()
                    melted = chart_data.melt('날짜', var_name='항목', value_name='실제값')
                    
                    def expand_info(item): return pd.Series(get_indicator_detail(item))
                    info_df = melted['항목'].apply(expand_info)
                    melted = pd.concat([melted, info_df], axis=1)

                    def get_val(row):
                        if row['항목'] in scaled:
                            min_v = df_final[row['항목']].min()
                            max_v = df_final[row['항목']].max()
                            if min_v == max_v: return 0
                            return (row['실제값'] - min_v) / (max_v - min_v) * 10
                        return row['실제값']
                    melted['표시값'] = melted.apply(get_val, axis=1)

                    # 차트 그리기
                    base = alt.Chart(melted).encode(x=alt.X('날짜:T', title='', axis=alt.Axis(format='%y/%m/%d', labelAngle=0)))
                    
                    lines = base.mark_line(point=True).encode(
                        y=alt.Y('표시값', title=''),
                        color=alt.Color('항목', scale=alt.Scale(domain=list(custom_colors.keys()), range=list(custom_colors.values())), legend=alt.Legend(orient='top', title=None)),
                        strokeDash=alt.StrokeDash('항목', scale=alt.Scale(domain=list(custom_dashes.keys()), range=list(custom_dashes.values())), legend=None),
                        tooltip=[
                            alt.Tooltip('날짜', title='📅 날짜', format='%y/%m/%d'),
                            alt.Tooltip('항목', title='📊 항목'),
                            alt.Tooltip('실제값', title='💰 값', format=','),
                            alt.Tooltip('기준:N', title='📏 기준'),
                            alt.Tooltip('의미:N', title='🔹 의미'),
                            alt.Tooltip('높을 때:N', title='🔺 높을때'),
                            alt.Tooltip('낮을 때:N', title='🔻 낮을때'),
                            alt.Tooltip('특징:N', title='✨ 특징'),
                            alt.Tooltip('시사점:N', title='💡 시사점')
                        ]
                    )
                    final_chart = lines

                    if show_labels:
                        text_data = melted if show_all_labels else melted[melted['날짜'] == melted.groupby('항목')['날짜'].transform('max')]
                        labels = alt.Chart(text_data).mark_text(align='left', dx=8, dy=-8, fontSize=11, fontWeight='bold').encode(
                            x='날짜:T', y='표시값', text=alt.Text('실제값', format=',.2f'), color=alt.value('black')
                        )
                        final_chart = final_chart + labels

                    st.altair_chart(final_chart.properties(height=400).interactive(), use_container_width=True)
                    
                    with st.expander(f"📋 {cat_name} 데이터 표 & 코멘트", expanded=True):
                        cols = list(selected)
                        if '📝비고' in df_final.columns: cols = ['📝비고'] + cols
                        st.dataframe(df_final[cols].style.format("{:,.2f}", subset=selected), use_container_width=True)
                    st.markdown("---")

    # ----------------------------------------------------
    # [3] 맨 아래: 심화 분석 (Deep Analysis)
    # ----------------------------------------------------
    st.markdown("### 🔍 심화 분석 (Deep Analysis)")
    
    col_ana1, col_ana2 = st.columns(2)
    
    # 1) 장단기 금리차
    with col_ana1:
        st.markdown("#### 📉 장단기 금리차 (경기 침체 경고)")
        cols = df_final.columns
        us_10y = next((c for c in cols if ("미국" in c and "10년" in c)), None)
        us_2y = next((c for c in cols if ("미국" in c and "2년" in c)), None)
        kr_10y = next((c for c in cols if ("한국" in c and "10년" in c)), None)
        kr_3y = next((c for c in cols if ("한국" in c and "3년" in c)), None)
        
        spread_data = pd.DataFrame(index=df_final.index)
        has_spread = False
        
        if us_10y and us_2y:
            spread_data['미국(10y-2y)'] = df_final[us_10y] - df_final[us_2y]
            has_spread = True
        if kr_10y and kr_3y:
            spread_data['한국(10y-3y)'] = df_final[kr_10y] - df_final[kr_3y]
            has_spread = True
            
        if has_spread:
            spread_melt = spread_data.reset_index().melt('날짜', var_name='종류', value_name='금리차')
            base = alt.Chart(spread_melt).encode(x='날짜:T')
            chart = base.mark_line(point=True).encode(
                y='금리차', color='종류', tooltip=['날짜', '종류', alt.Tooltip('금리차', format='.2f')]
            )
            rule = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='red').encode(y='y')
            st.altair_chart((chart + rule).interactive(), use_container_width=True)
            st.caption("💡 0 아래(음수)로 내려가면 '경기 침체' 위험 신호입니다.")
        else:
            st.warning("금리 데이터가 부족하여 계산할 수 없습니다.")

    # 2) 상관관계 분석
    with col_ana2:
        st.markdown("#### 🔗 상관관계 분석")
        valid_cols = [c for c in df_final.columns if df_final[c].dtype != 'object']
        
        sel_1 = st.selectbox("지표 1", valid_cols, index=0 if len(valid_cols)>0 else None)
        sel_2 = st.selectbox("지표 2", valid_cols, index=1 if len(valid_cols)>1 else None)
        
        if sel_1 and sel_2:
            corr_val = df_final[sel_1].corr(df_final[sel_2])
            st.markdown(f"👉 **상관계수: {corr_val:.2f}**")
            
            # 정규화
            norm_data = df_final[[sel_1, sel_2]].dropna()
            if not norm_data.empty:
                norm_data = (norm_data - norm_data.min()) / (norm_data.max() - norm_data.min())
                norm_melt = norm_data.reset_index().melt('날짜', var_name='지표', value_name='정규화값(0~1)')
                
                c = alt.Chart(norm_melt).mark_line().encode(
                    x='날짜:T', y='정규화값(0~1)', color='지표', tooltip=['날짜', '지표', alt.Tooltip('정규화값(0~1)', format='.2f')]
                )
                st.altair_chart(c.interactive(), use_container_width=True)
                st.caption("💡 두 지표의 흐름을 비교하기 위해 0~1로 맞춘 차트입니다.")
else:
    st.error("데이터가 없습니다.")