import { useState } from 'react';
import { apiService } from '../api/client';
import { useReconciliationStore } from '../store/reconciliationStore';

export const useFileUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  const { setCrmFile, addReportFile, setConfigFile } = useReconciliationStore();

  const uploadCrm = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const data = await apiService.uploadCrm(file);
      setCrmFile({
        file_id: data.file_id,
        filename: data.filename,
        source_type: data.source_type
      });
      return data;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'CRM upload failed';
      setUploadError(msg);
      throw new Error(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const uploadReports = async (files: File[]) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const data = await apiService.uploadReports(files);
      data.uploaded_files.forEach((uploaded: any) => {
        addReportFile({
          file_id: uploaded.file_id,
          filename: uploaded.filename,
          source_type: uploaded.source_type
        });
      });
      return data;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Reports upload failed';
      setUploadError(msg);
      throw new Error(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const uploadConfig = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const data = await apiService.uploadConfig(file);
      setConfigFile({
        file_id: data.file_id,
        filename: data.filename,
        source_type: data.source_type
      });
      return data;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Config upload failed';
      setUploadError(msg);
      throw new Error(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return {
    isUploading,
    uploadError,
    uploadCrm,
    uploadReports,
    uploadConfig
  };
};
