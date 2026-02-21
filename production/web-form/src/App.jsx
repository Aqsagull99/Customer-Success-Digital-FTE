import SupportForm from './components/SupportForm'

function App() {
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-2xl mx-auto mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">TechCorp Support</h1>
        <p className="mt-2 text-gray-600">AI-powered 24/7 customer support</p>
      </div>
      <SupportForm apiEndpoint="/api/support/submit" />
    </div>
  )
}

export default App
