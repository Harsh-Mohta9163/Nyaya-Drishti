import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './tailwind-generated.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
