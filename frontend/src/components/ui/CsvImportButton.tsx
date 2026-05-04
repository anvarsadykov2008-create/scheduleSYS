import React, { useRef, useState } from 'react';
import { useLang } from '../../context/LanguageContext';
import { apiClient } from '../../api/client';
import { FileUp, CheckCircle, AlertCircle } from 'lucide-react';
import Button from './Button';

interface CsvImportButtonProps {
    endpoint: string;
    onSuccess?: () => void;
}

const CsvImportButton: React.FC<CsvImportButtonProps> = ({ endpoint, onSuccess }) => {
    const { t } = useLang();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setLoading(true);
        setStatus('idle');
        setMessage('');

        try {
            console.log(`Starting import to ${endpoint}...`);
            const res = await apiClient.postFile<{ message: string; errors: string[] }>(endpoint, file);
            console.log("Import result:", res);
            
            if (res.errors && res.errors.length > 0) {
                setStatus('error');
                setMessage(`${res.message}. Ошибок: ${res.errors.length}`);
                console.error("CSV Import Errors:", res.errors);
            } else {
                setStatus('success');
                setMessage(res.message);
                if (onSuccess) onSuccess();
            }
        } catch (err: unknown) {
            console.error("Import request failed:", err);
            setStatus('error');
            const errorMsg = err instanceof Error ? err.message : t.importError;
            setMessage(errorMsg);
        } finally {
            setLoading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
            
            // Сбросить статус через 5 секунд
            setTimeout(() => {
                setStatus('idle');
                setMessage('');
            }, 5000);
        }
    };

    return (
        <div className="relative inline-block">
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".csv"
                className="hidden"
            />
            <Button
                onClick={handleClick}
                loading={loading}
                variant="secondary"
                className={`flex items-center gap-2 ${
                    status === 'success' ? 'border-museum-success text-museum-success' : 
                    status === 'error' ? 'border-museum-danger text-museum-danger' : ''
                }`}
                title={message}
            >
                {status === 'idle' && (
                    <>
                        <FileUp className="h-4 w-4" />
                        <span>{t.importCsv}</span>
                    </>
                )}
                {status === 'success' && (
                    <>
                        <CheckCircle className="h-4 w-4" />
                        <span className="max-w-[150px] truncate">{message || t.importSuccess}</span>
                    </>
                )}
                {status === 'error' && (
                    <>
                        <AlertCircle className="h-4 w-4" />
                        <span className="max-w-[150px] truncate">{message || t.importError}</span>
                    </>
                )}
            </Button>
        </div>
    );
};

export default CsvImportButton;
