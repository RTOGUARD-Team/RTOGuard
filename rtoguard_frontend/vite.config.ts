import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({plugins:[react()],server:{proxy:{'/api':'http://localhost:8000','/rto':'http://localhost:8000'}}})
