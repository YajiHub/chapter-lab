import { Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth'
import { Layout } from './components/Layout'
import { RequireRole } from './components/RequireRole'
import Admin from './pages/Admin'
import Dashboard from './pages/Dashboard'
import LessonForm from './pages/LessonForm'
import Lessons from './pages/Lessons'
import NotFound from './pages/NotFound'
import Placeholder from './pages/Placeholder'
import SignIn from './pages/SignIn'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/signin" element={<SignIn />} />
          <Route element={<RequireRole role="student" />}>
            <Route index element={<Dashboard />} />
            <Route path="lessons" element={<Lessons />} />
            <Route path="lessons/new" element={<LessonForm />} />
            <Route path="lessons/:lessonId/edit" element={<LessonForm />} />
            <Route path="packs" element={<Placeholder title="Study packs" />} />
            <Route path="packs/:packId" element={<Placeholder title="Study pack" />} />
            <Route path="attempts/:attemptId" element={<Placeholder title="Attempt results" />} />
          </Route>
          <Route element={<RequireRole role="admin" />}>
            <Route path="admin" element={<Admin />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
