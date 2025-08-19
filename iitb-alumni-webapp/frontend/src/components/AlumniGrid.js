import React, { useMemo, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import './AlumniGrid.css';

const AlumniGrid = ({ alumni, onRowClick }) => {
  console.log('AlumniGrid render:', {
    alumniCount: alumni ? alumni.length : 'null',
    firstAlumni: alumni?.[0],
    hasFirstJob: alumni?.[0]?.firstJob
  });

  const columnDefs = useMemo(() => [
    {
      headerName: 'Name',
      field: 'name',
      width: 200,
      minWidth: 150,
      pinned: 'left',
      cellRenderer: (params) => (
        <div className="name-cell">
          <div className="name">{params.value || '-'}</div>
        </div>
      )
    },
    {
      headerName: 'Grad Year',
      field: 'grad_yr',
      width: 100,
      minWidth: 80,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Current Company',
      field: 'firstJob.comp',
      width: 180,
      minWidth: 150,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Current Role',
      field: 'firstJob.title',
      width: 200,
      minWidth: 150,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Location',
      field: 'firstJob.loc',
      width: 180,
      minWidth: 120,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Sector',
      field: 'firstJob.sector',
      width: 140,
      minWidth: 100,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Seniority',
      field: 'firstJob.seniority',
      width: 150,
      minWidth: 120,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Company Size',
      field: 'firstJob.company_size',
      width: 140,
      minWidth: 100,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'Remote Type',
      field: 'firstJob.remote_type',
      width: 120,
      minWidth: 100,
      cellRenderer: (params) => params.value || '-'
    },
    {
      headerName: 'LinkedIn',
      field: 'link_ln',
      width: 100,
      minWidth: 80,
      cellRenderer: (params) =>
        params.value ? (
          <a
            href={params.value}
            target="_blank"
            rel="noopener noreferrer"
            className="linkedin-link"
            onClick={(e) => e.stopPropagation()}
          >
            view
          </a>
        ) : '-'
    }
  ], []);

  const defaultColDef = useMemo(() => ({
    sortable: true,
    filter: true,
    resizable: true,
    suppressMovable: false,
    floatingFilter: false, // Can be enabled for advanced filtering
  }), []);

  const onRowClicked = useCallback((event) => {
    console.log('Row clicked:', event.data);
    if (onRowClick) {
      onRowClick(event.data);
    }
  }, [onRowClick]);

  const gridOptions = useMemo(() => ({
    animateRows: true,
    rowHeight: 50,
    headerHeight: 45,
    suppressHorizontalScroll: false,
    suppressMenuHide: false,
    enableRangeSelection: false,
    enableCellSelection: false,
    suppressRowClickSelection: true,
    rowSelection: 'single',
    // Performance settings
    rowBuffer: 10, // Number of rows to render outside viewable area
    maxBlocksInCache: 2,
    maxConcurrentDatasourceRequests: 2,
    // Scrolling
    suppressScrollOnNewData: false,
    alwaysShowHorizontalScroll: false,
    alwaysShowVerticalScroll: false,
  }), []);

  // Always show debug info for now
  const showDebugInfo = true;

  if (!alumni || alumni.length === 0) {
    return (
      <div className="alumni-grid-container" style={{ background: 'rgba(255,0,0,0.2)', border: '2px solid red' }}>
        <div style={{ padding: '2rem', textAlign: 'center', color: '#fff', fontSize: '18px' }}>
          <h2>Debug Info:</h2>
          <p>Alumni data: {alumni ? `${alumni.length} records` : 'null/undefined'}</p>
          <p>Type: {typeof alumni}</p>
          <p>{!alumni ? 'Loading alumni data...' : 'No alumni data found'}</p>
        </div>
      </div>
    );
  }

  // Show debug info if needed
  if (showDebugInfo) {
    return (
      <div className="alumni-grid-container" style={{ background: 'rgba(0,255,0,0.2)', border: '2px solid green' }}>
        <div style={{ padding: '2rem', color: '#fff' }}>
          <h2>Grid Debug Info:</h2>
          <p>Alumni count: {alumni.length}</p>
          <p>First alumni: {alumni[0]?.name}</p>
          <p>Has first job: {alumni[0]?.firstJob ? 'Yes' : 'No'}</p>
          <p>First job company: {alumni[0]?.firstJob?.comp}</p>

          {/* Simple HTML table to verify data */}
          <div style={{ marginTop: '2rem', maxHeight: '400px', overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: '#fff' }}>
              <thead>
                <tr style={{ background: 'rgba(0,0,0,0.5)' }}>
                  <th style={{ border: '1px solid #333', padding: '8px' }}>Name</th>
                  <th style={{ border: '1px solid #333', padding: '8px' }}>Grad Year</th>
                  <th style={{ border: '1px solid #333', padding: '8px' }}>Company</th>
                  <th style={{ border: '1px solid #333', padding: '8px' }}>Role</th>
                </tr>
              </thead>
              <tbody>
                {alumni.slice(0, 20).map((person, index) => (
                  <tr key={index} style={{ background: index % 2 === 0 ? 'rgba(255,255,255,0.05)' : 'transparent' }}>
                    <td style={{ border: '1px solid #333', padding: '8px' }}>{person.name}</td>
                    <td style={{ border: '1px solid #333', padding: '8px' }}>{person.grad_yr || '-'}</td>
                    <td style={{ border: '1px solid #333', padding: '8px' }}>{person.firstJob?.comp || '-'}</td>
                    <td style={{ border: '1px solid #333', padding: '8px' }}>{person.firstJob?.title || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            onClick={() => console.log('Alumni data:', alumni.slice(0, 5))}
            style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#00ff88', color: '#000' }}
          >
            Log Data to Console
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="alumni-grid-container">
      <div className="alumni-grid ag-theme-quartz">
        <AgGridReact
          rowData={alumni}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          gridOptions={gridOptions}
          onRowClicked={onRowClicked}
          // Size and layout
          domLayout="normal"
          // Performance
          suppressLoadingOverlay={false}
          loadingOverlayComponent="Loading..."
          // Callbacks
          onGridReady={(params) => {
            console.log('Grid ready with', alumni.length, 'rows');
            // Auto-size columns to fit content
            params.api.sizeColumnsToFit();
          }}
          onFirstDataRendered={(params) => {
            console.log('First data rendered');
            // Optionally auto-size columns after data loads
            params.api.sizeColumnsToFit();
          }}
        />
      </div>
    </div>
  );
};

export default AlumniGrid;