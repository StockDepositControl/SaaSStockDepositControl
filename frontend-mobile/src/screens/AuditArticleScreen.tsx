import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Alert,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useMobileDataClient } from '../context/DataContext';
import { ArticuloAuditorView } from '../types/article';
import { AuditMotive } from '../types/audit';
import { SearchScannerBar } from '../components/audit/SearchScannerBar';
import { EmptyAuditState } from '../components/audit/EmptyAuditState';
import { BarcodeScannerModal } from '../components/audit/BarcodeScannerModal';
import { ArticleInspectionCard } from '../components/audit/ArticleInspectionCard';
import { CountedQuantityInput } from '../components/audit/CountedQuantityInput';
import { MotiveSelectSheet } from '../components/audit/MotiveSelectSheet';
import { DeltaCalculator } from '../services/domain/DeltaCalculator';
import { AuditValidator } from '../services/domain/AuditValidator';
import { Icon } from '../components/ui/Icon';
import { colors } from '../utils/designTokens';

interface AuditArticleScreenProps {
  initialArticleId?: string | null;
  onAuditCompleted?: () => void;
}

export const AuditArticleScreen: React.FC<AuditArticleScreenProps> = ({
  initialArticleId,
  onAuditCompleted,
}) => {
  const client = useMobileDataClient();

  const [query, setQuery] = useState('');
  const [selectedArticle, setSelectedArticle] = useState<ArticuloAuditorView | null>(null);
  const [countedText, setCountedText] = useState('');
  const [selectedMotive, setSelectedMotive] = useState<AuditMotive | null>(null);
  const [observation, setObservation] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isScannerOpen, setIsScannerOpen] = useState(false);

  // Load article by ID or barcode
  const loadArticle = useCallback(
    async (searchKey: string) => {
      setIsSearching(true);
      setSearchError(null);
      setFormError(null);
      try {
        const results = await client.searchArticles(searchKey);
        if (results.length > 0) {
          const item = results[0];
          let effectiveStock = item.stock_real;

          try {
            const stockPos = await client.getArticleStockPosition(item.id_articulo);
            if (typeof stockPos.stock_real === 'number') {
              effectiveStock = stockPos.stock_real;
            }
          } catch {
            // Fallback to item.stock_real if position call fails
          }

          const enrichedItem = {
            ...item,
            stock_real: effectiveStock,
          };

          setSelectedArticle(enrichedItem);
          setCountedText(String(effectiveStock));
          setSelectedMotive(null);
          setObservation('');
        } else {
          setSearchError('No se encontró ningún artículo para el código o nombre ingresado.');
          setSelectedArticle(null);
        }
      } catch (err) {
        setSearchError('Error al buscar el artículo. Intentá nuevamente.');
        setSelectedArticle(null);
      } finally {
        setIsSearching(false);
      }
    },
    [client]
  );

  useEffect(() => {
    if (initialArticleId) {
      loadArticle(initialArticleId);
    }
  }, [initialArticleId, loadArticle]);

  const handleSearch = () => {
    if (query.trim()) {
      loadArticle(query.trim());
    }
  };

  const handleBarcodeScanned = (barcode: string) => {
    setQuery(barcode);
    loadArticle(barcode);
  };

  const handleCancel = () => {
    setSelectedArticle(null);
    setQuery('');
    setCountedText('');
    setSelectedMotive(null);
    setObservation('');
    setSearchError(null);
    setFormError(null);
  };

  // Delta calculations for variance enforcement
  const stockBaseline = selectedArticle?.stock_real ?? 0;
  const numCounted = countedText === '' ? stockBaseline : Number(countedText) || 0;
  const delta = DeltaCalculator.compute(stockBaseline, numCounted);

  const handleSaveAudit = async () => {
    if (!selectedArticle) return;

    setFormError(null);
    const validation = AuditValidator.validateForm({
      rawCount: countedText,
      requiresMotive: delta.requiresMotive,
      motiveId: selectedMotive?.id,
      observation,
    });

    if (!validation.isValid) {
      setFormError(validation.errorMessage || 'Verificá los datos ingresados.');
      return;
    }

    setIsSubmitting(true);
    try {
      await client.registerAudit({
        id_articulo: selectedArticle.id_articulo,
        stock_fisico_contado: numCounted,
        cantidad_afectada: delta.affectedQuantity,
        tipo_accion: delta.actionType,
        motive_id: selectedMotive?.id || (delta.actionType === 'Sin Acción' ? 'CONTEO_REGULAR' : undefined),
        observation: observation.trim() || undefined,
      });

      Alert.alert(
        'Auditoría registrada',
        `El artículo "${selectedArticle.des_articulo}" se guardó exitosamente.`,
        [
          {
            text: 'Aceptar',
            onPress: () => {
              handleCancel();
              if (onAuditCompleted) onAuditCompleted();
            },
          },
        ]
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al registrar la auditoría.';
      setFormError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSaveDisabled =
    isSubmitting ||
    countedText === '' ||
    (delta.requiresMotive && !selectedMotive);

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      {/* Search & Scanner Toolbar */}
      <SearchScannerBar
        query={query}
        onChangeQuery={setQuery}
        onSearch={handleSearch}
        onOpenScanner={() => setIsScannerOpen(true)}
        isLoading={isSearching}
      />

      {isSearching && (
        <View style={styles.loadingBox}>
          <ActivityIndicator color={colors.primary[500]} size="small" />
          <Text style={styles.loadingText}>Buscando artículo...</Text>
        </View>
      )}

      {/* Empty State / Not Found Prompt */}
      {!selectedArticle && !isSearching && (
        <EmptyAuditState errorMessage={searchError} />
      )}

      {/* Selected Article Audit Form */}
      {selectedArticle && !isSearching && (
        <ScrollView
          style={styles.scrollArea}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* Article Inspection Card (image_3) */}
          <ArticleInspectionCard article={selectedArticle} />

          {/* Physical Adjustment Registry Form (image_4) */}
          <View style={styles.formContainer}>
            {formError && (
              <View style={styles.formErrorCard}>
                <Icon name="alert-circle" size={18} color="#DC2626" />
                <Text style={styles.formErrorText}>{formError}</Text>
              </View>
            )}

            {/* Field 1: Cantidad Contada */}
            <CountedQuantityInput
              value={countedText}
              onChangeValue={(val) => {
                setCountedText(val);
                setFormError(null);
              }}
              stockBaseline={stockBaseline}
            />

            {/* Field 2: Motivo */}
            <MotiveSelectSheet
              selectedMotiveId={selectedMotive?.id}
              onSelectMotive={(m) => {
                setSelectedMotive(m);
                setFormError(null);
              }}
              requiresMotive={delta.requiresMotive}
              actionType={delta.actionType}
              hasError={delta.requiresMotive && !selectedMotive && !!formError}
            />

            {/* Field 3: Observación (opcional) */}
            <View style={styles.observationGroup}>
              <View style={styles.observationLabelRow}>
                <Text style={styles.observationLabel}>Observación </Text>
                <Text style={styles.optionalLabel}>(opcional)</Text>
              </View>
              <TextInput
                style={styles.observationInput}
                value={observation}
                onChangeText={setObservation}
                placeholder="Notas u observaciones del conteo..."
                placeholderTextColor={colors.text.disabled}
                multiline
                numberOfLines={3}
                maxLength={255}
                textAlignVertical="top"
              />
            </View>

            {/* Primary Action Button: Guardar auditoría */}
            <Pressable
              onPress={handleSaveAudit}
              disabled={isSaveDisabled}
              style={({ pressed }) => [
                styles.saveButton,
                pressed && styles.saveButtonPressed,
                isSaveDisabled && styles.saveButtonDisabled,
              ]}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <>
                  <Icon name="check" size={18} color={isSaveDisabled ? '#94A3B8' : '#FFFFFF'} />
                  <Text
                    style={[
                      styles.saveButtonText,
                      isSaveDisabled && styles.saveButtonTextDisabled,
                    ]}
                  >
                    Guardar auditoría
                  </Text>
                </>
              )}
            </Pressable>

            {/* Secondary Action Button: Cancelar */}
            <Pressable
              onPress={handleCancel}
              style={({ pressed }) => [
                styles.cancelButton,
                pressed && styles.cancelButtonPressed,
              ]}
            >
              <Text style={styles.cancelButtonText}>Cancelar</Text>
            </Pressable>
          </View>
        </ScrollView>
      )}

      {/* Camera / Barcode Scanner Modal */}
      <BarcodeScannerModal
        isVisible={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onScan={handleBarcodeScanned}
      />
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.base,
  },
  loadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
    color: colors.text.muted,
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  formContainer: {
    paddingHorizontal: 16,
  },
  formErrorCard: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  formErrorText: {
    fontSize: 12,
    color: '#B91C1C',
    fontWeight: '600',
    flex: 1,
  },
  observationGroup: {
    marginBottom: 20,
  },
  observationLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  observationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  optionalLabel: {
    fontSize: 12,
    color: colors.text.disabled,
  },
  observationInput: {
    minHeight: 84,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    padding: 12,
    fontSize: 14,
    color: colors.text.primary,
  },
  saveButton: {
    height: 48,
    borderRadius: 12,
    backgroundColor: colors.primary[500],
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 10,
  },
  saveButtonPressed: {
    backgroundColor: colors.primary[600],
  },
  saveButtonDisabled: {
    backgroundColor: '#E2E8F0',
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  saveButtonTextDisabled: {
    color: '#94A3B8',
  },
  cancelButton: {
    height: 48,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButtonPressed: {
    backgroundColor: '#F1F5F9',
  },
  cancelButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
  },
});
