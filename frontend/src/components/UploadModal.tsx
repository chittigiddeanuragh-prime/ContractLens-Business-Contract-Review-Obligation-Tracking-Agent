import React, { useState } from 'react';
import { Upload, X, FileText, AlertTriangle, Loader2 } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (contractId: string, versionId: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState<string>('');
  const [counterparty, setCounterparty] = useState<string>('');
  const [uploading, setUploading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/contracts/${contractId}/versions/${versionId}`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === 'ready' || data.status === 'ready_with_warnings' || data.status === 'parsed' || data.status === 'segmented') {
          clearInterval(interval);
          setUploading(false);
          onUploadSuccess(contractId, versionId);
          onClose();
        } else if (data.status === 'scanned_unsupported') {
          clearInterval(interval);
          setUploading(false);
          setErrorMessage(data.error_message || 'This PDF looks scanned or image-only.');
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setUploading(false);
          setErrorMessage(data.error_message || 'Parsing failed.');
        } else {
          setStatusMessage(`Processing pipeline stage: ${data.status}...`);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setErrorMessage(null);
    setStatusMessage('Uploading contract PDF...');

    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (counterparty) formData.append('counterparty', counterparty);

    try {
      const res = await fetch('/api/v1/contracts', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error?.message || errData.detail || 'Upload failed');
      }

      const data = await res.json();
      pollVersionStatus(data.contract_id, data.version_id);
    } catch (err: any) {
      setUploading(false);
      setErrorMessage(err.message || 'An error occurred during upload.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 relative">
        <button
          onClick={onClose}
          disabled={uploading}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
          <Upload className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          Upload Contract Document
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-5">
          Upload a contract PDF for structure segmentation, key field extraction, and market risk analysis.
        </p>

        <form onSubmit={handleUpload} className="space-y-4">
          {/* Drag & Drop Zone */}
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-indigo-500 dark:hover:border-indigo-400 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-50 dark:bg-slate-800/40">
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
              <Upload className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
              {file ? (
                <div className="text-sm font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              ) : (
                <>
                  <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    Click to browse or drop PDF here
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">Max size: 25 MB • PDF text documents only</span>
                </>
              )}
            </label>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Contract Title</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Master Services Agreement 2026"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={uploading}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Counterparty (Optional)</label>
            <input
              type="text"
              value={counterparty}
              onChange={(e) => setCounterparty(e.target.value)}
              placeholder="e.g. Orion Cloud Services LLC"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={uploading}
            />
          </div>

          {errorMessage && (
            <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{errorMessage}</span>
            </div>
          )}

          {uploading && (
            <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900 text-xs text-indigo-700 dark:text-indigo-300 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin shrink-0 text-indigo-600" />
              <span className="font-semibold">{statusMessage}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="px-5 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 flex items-center gap-2 shadow-md shadow-indigo-600/20 transition active:scale-95"
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
