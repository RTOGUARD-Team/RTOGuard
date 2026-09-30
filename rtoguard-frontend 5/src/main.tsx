import React from 'react'
import {createRoot} from 'react-dom/client'
import {BrowserRouter} from 'react-router-dom'
import App from './App'
import {DemoProvider} from './hooks/useDemo'
import './index.css'
createRoot(document.getElementById('root')!).render(<React.StrictMode><BrowserRouter><DemoProvider><App/></DemoProvider></BrowserRouter></React.StrictMode>)
