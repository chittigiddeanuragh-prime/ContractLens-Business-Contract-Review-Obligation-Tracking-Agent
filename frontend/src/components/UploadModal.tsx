import React, { useState } from 'react';
import { Upload, X, FileText, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (contractId: str, versionId: str) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState<string>('');
  const [counterparty, setCounterparty] = useState<string>('');
  const [uploading, setUploading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDuplicate, setIsDuplicate] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setErrorMessage('Only PDF files are supported.');
        return;
      }
      if (selected.size > 25 * 1024 * 1024) {
        setErrorMessage('File size exceeds the 25 MB limit.');
        return;
      }
      setFile(selected);
      setErrorMessage(null);
      if (!name) {
        setName(selected.name.replace(/\.pdf$/i, ''));
      }
    }
  };

  const pollVersionStatus = async (contractId: string, versionId: string) => {
    setStatusMessage('Parsing contract PDF and building canonical text...');
    const startTime = Date.now();

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === 'parsed') {
          clearInterval(interval);
          setUploading(false);
          onUploadSuccess(contractId, versionId);
          onClose();
        } else if (data.status === 'scanned_unsupported') {
          clearInterval(interval);
          setUploading(false);
          setErrorMessage(data.error_message || 'This PDF looks scanned or image-only. OCR support is on the roadmap.');
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setUploading(false);
          setErrorMessage(data.error_message || 'Failed to parse PDF.');
        }

        // Timeout fallback after 30s
        if (Date.now() - startTime > 30000) {
          clearInterval(interval);
          setUploading(false);
          setErrorMessage('Parsing timed out. Please refresh and check status.');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage('Please select a PDF contract file to upload.');
      return;
    }

    setUploading(true);
    setErrorMessage(null);
    setStatusMessage('Uploading contract file to storage...');

    const formData = new FormData();
    formData.append('file', file);
    if (name.trim()) formData.append('name', name.trim());
    if (counterparty.trim()) formData.append('counterparty', counterparty.trim());

    try {
      const res = await fetch('/api/v1/contracts', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error?.message || 'Failed to upload contract.');
      }

      if (data.duplicate) {
        setIsDuplicate(true);
        setStatusMessage('Duplicate contract version detected (SHA-256 matched).');
      }

      await pollVersionStatus(data.contract_id, data.version_id);
    } catch (err: any) {
      setUploading(false);
      setErrorMessage(err.message || 'Upload failed.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          disabled={uploading}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-white mb-1">Upload Contract PDF</h3>
        <p className="text-xs text-slate-400 mb-6">
          Upload a contract for clause segmentation, key field extraction, and obligation timeline analysis.
        </p>

        <form onSubmit={handleUpload} className="space-y-4">
          {/* Drag & Drop Zone */}
          <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-800/40">
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
              <Upload className="w-8 h-8 text-blue-400" />
              {file ? (
                <div className="text-sm font-semibold text-blue-300 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              ) : (
                <>
                  <span className="text-sm font-medium text-slate-200">
                    Click to browse or drop PDF here
                  </span>
                  <span className="text-xs text-slate-400">Max size: 25 MB • PDF text documents only</span>
                </>
              )}
            </label>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Contract Title</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Master Services Agreement 2026"
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-blue-500"
              disabled={uploading}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Counterparty (Optional)</label>
            <input
              type="text"
              value={counterparty}
              onChange={(e) => setCounterparty(e.target.value)}
              placeholder="e.g. Orion Cloud Services LLC"
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-blue-500"
              disabled={uploading}
            />
          </div>

          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {uploading && (
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-xs text-blue-300 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="px-5 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 flex items-center gap-2"
            >
              {uploading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {uploading ? 'Processing...' : 'Upload & Parse'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
