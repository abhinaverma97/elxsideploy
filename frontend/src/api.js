import axios from 'axios'

const client = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' }
})

export const addRequirement = (r) => client.post('/requirements/', r)
export const analyzeRequirement = (text, deviceType) =>
  client.post('/requirements/analyze', { text, device_type: deviceType })
export const buildDesign = (deviceType) => client.post('/design/build/', null, { params: { device_type: deviceType } })
export const generateDesignDetails = (deviceType) => client.post('/design/generate-details/', null, { params: { device_type: deviceType } })
export const getDetailedDesign = (deviceType) => client.get('/design/detailed-design/', { params: { device_type: deviceType } })
export const getVerificationMatrix = (deviceType) => client.get('/design/verification-matrix/', { params: { device_type: deviceType } })

export const runSimulation = (deviceType, steps = 10, fidelity = 'L2') =>
  client.post('/simulation/run/', null, { params: { device_type: deviceType, steps, fidelity } })
export const runFaultySimulation = (deviceType, parameter, bias, steps = 10) =>
  client.post('/simulation/fault/', null, { params: { device_type: deviceType, parameter, bias, steps } })
export const generateCodeRepo = () => client.post('/codegen/generate/')
export const getTraceability = () => client.get('/export/traceability/').then(r => r.data)
export const validateDesign = () => client.post('/export/validate/')

export default client