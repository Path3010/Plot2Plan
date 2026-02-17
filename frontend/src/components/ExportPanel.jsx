export default function ExportPanel({ projectId, onGenerate3D }) {
    return (
        <div className="export-bar">
            <a
                className="btn btn-secondary btn-sm"
                href={`/api/download-dxf/${projectId}`}
                download
            >
                Download DXF
            </a>
            <button className="btn btn-secondary btn-sm" onClick={onGenerate3D}>
                Generate 3D
            </button>
            <a
                className="btn btn-secondary btn-sm"
                href={`/api/3d-model/${projectId}`}
                download
            >
                Download 3D Model
            </a>
        </div>
    )
}
