import { useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Case } from '@/types';
import { cn } from '@/lib/utils';

interface PDFUploadProps {
  onUpload: (file: File) => Promise<Case>;
  maxSizeMB?: number;
}

export default function PDFUpload({ onUpload, maxSizeMB = 50 }: PDFUploadProps) {
  const { t } = useTranslation();
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.type !== 'application/pdf') return t('upload.pdfOnly');
    if (file.size > maxSizeMB * 1024 * 1024) return t('upload.maxSize');
    return null;
  };

  const handleFile = useCallback(async (file: File) => {
    const err = validateFile(file);
    if (err) { setError(err); return; }

    setError('');
    setUploading(true);
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(p => Math.min(p + Math.random() * 20, 90));
    }, 300);

    try {
      await onUpload(file);
      setProgress(100);
      setSuccess(true);
      setTimeout(() => { setSuccess(false); setProgress(0); }, 2000);
    } catch {
      setError('Upload failed. Please try again.');
    } finally {
      clearInterval(progressInterval);
      setUploading(false);
    }
  }, [onUpload, maxSizeMB]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        'relative cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all duration-200',
        dragActive
          ? 'border-blue-400 bg-blue-500/5'
          : 'border-slate-700 hover:border-slate-600 bg-slate-800/20',
        uploading && 'pointer-events-none'
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        className="hidden"
      />

      {success ? (
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="flex flex-col items-center gap-2">
          <CheckCircle size={40} className="text-green-400" />
          <p className="text-sm text-green-400 font-medium">Upload successful!</p>
        </motion.div>
      ) : (
        <>
          <div className="mb-3 flex justify-center">
            <div className={cn('rounded-xl p-3', dragActive ? 'bg-blue-500/10' : 'bg-slate-800/50')}>
              {uploading ? <FileText size={32} className="text-blue-400" /> : <Upload size={32} className="text-slate-500" />}
            </div>
          </div>
          <p className="text-sm font-medium text-slate-300">{t('upload.dragDrop')}</p>
          <p className="mt-1 text-xs text-slate-500">{t('upload.orBrowse')}</p>
          <p className="mt-2 text-[10px] text-slate-600">{t('upload.maxSize')}</p>
        </>
      )}

      {uploading && (
        <div className="mt-4">
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-700">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <p className="mt-2 text-xs text-blue-400">{t('upload.uploading')} {Math.round(progress)}%</p>
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-center justify-center gap-1.5 text-xs text-red-400">
          <X size={12} />
          {error}
        </div>
      )}
    </div>
  );
}
