import { createGlobalStyle } from 'styled-components';

export const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body {
    height: 100%;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    background-color: #ffffff;
    color: #111827;
    line-height: 1.5;
  }

  #root {
    height: 100%;
    min-height: 100vh;
  }

  /* 스크롤바 스타일링 */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: #f3f4f6;
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }

  /* 버튼 기본 스타일 제거 */
  button {
    border: none;
    background: none;
    cursor: pointer;
    font-family: inherit;
  }

  /* 입력 필드 기본 스타일 제거 */
  input, textarea, select {
    border: none;
    background: none;
    font-family: inherit;
    outline: none;
  }

  /* 링크 스타일 제거 */
  a {
    text-decoration: none;
    color: inherit;
  }

  /* 리스트 스타일 제거 */
  ul, ol {
    list-style: none;
  }

  /* 이미지 기본 설정 */
  img {
    max-width: 100%;
    height: auto;
  }

  /* 테이블 기본 설정 */
  table {
    border-collapse: collapse;
    border-spacing: 0;
  }
`;