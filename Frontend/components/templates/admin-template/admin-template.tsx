/**
 * Admin Template - Administrative interface layout
 * 
 * This template provides the layout structure for admin pages.
 * It includes sidebar navigation, main content area, and consistent
 * styling for administrative functionality.
 */

import { ReactNode } from "react"

interface AdminTemplateProps {
  /** Admin sidebar navigation */
  sidebar?: ReactNode
  /** Page header with title and actions */
  pageHeader?: ReactNode
  /** Main admin content */
  children: ReactNode
  /** Page-level actions (export, settings, etc.) */
  pageActions?: ReactNode
  /** Breadcrumb navigation */
  breadcrumbs?: ReactNode
  /** Custom className for template styling */
  className?: string
}

export function AdminTemplate({
  sidebar,
  pageHeader,
  children,
  pageActions,
  breadcrumbs,
  className
}: AdminTemplateProps) {
  return (
    <div className={`admin-template ${className || ''}`}>
      <div className="admin-layout flex min-h-screen bg-gray-50">
        {/* Admin Sidebar */}
        {sidebar && (
          <aside className="admin-sidebar w-64 bg-white shadow-sm">
            {sidebar}
          </aside>
        )}

        {/* Main Content Area */}
        <main className={`admin-main flex-1 ${sidebar ? 'ml-0' : ''}`}>
          {/* Page Header */}
          <header className="admin-header bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="header-content">
                {breadcrumbs && (
                  <nav className="breadcrumbs mb-2">
                    {breadcrumbs}
                  </nav>
                )}
                {pageHeader}
              </div>
              {pageActions && (
                <div className="page-actions">
                  {pageActions}
                </div>
              )}
            </div>
          </header>

          {/* Page Content */}
          <div className="admin-content p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}