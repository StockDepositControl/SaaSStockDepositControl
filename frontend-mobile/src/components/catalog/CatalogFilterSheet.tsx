import React from 'react';
import {
  View,
  Text,
  Pressable,
  Modal,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

export interface CatalogFilterState {
  status: 'all' | 'pending' | 'audited';
  criticalOnly: boolean;
}

interface CatalogFilterSheetProps {
  isVisible: boolean;
  onClose: () => void;
  filters: CatalogFilterState;
  onApplyFilters: (newFilters: CatalogFilterState) => void;
}

export const CatalogFilterSheet: React.FC<CatalogFilterSheetProps> = ({
  isVisible,
  onClose,
  filters,
  onApplyFilters,
}) => {
  const [localFilters, setLocalFilters] = React.useState<CatalogFilterState>(filters);

  React.useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleApply = () => {
    onApplyFilters(localFilters);
    onClose();
  };

  const handleReset = () => {
    const resetState: CatalogFilterState = { status: 'all', criticalOnly: false };
    setLocalFilters(resetState);
    onApplyFilters(resetState);
    onClose();
  };

  return (
    <Modal visible={isVisible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <Pressable style={styles.backdrop} onPress={onClose} />
        <SafeAreaView style={styles.sheet}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Filtros del catálogo</Text>
            <Pressable onPress={onClose} style={styles.closeBtn} hitSlop={8}>
              <Icon name="x" size={18} color={colors.text.secondary} />
            </Pressable>
          </View>

          <View style={styles.content}>
            {/* Filter by Status */}
            <Text style={styles.sectionLabel}>ESTADO DE AUDITORÍA</Text>
            <View style={styles.optionsRow}>
              {(['all', 'pending', 'audited'] as const).map((st) => {
                const isSelected = localFilters.status === st;
                const label = st === 'all' ? 'Todos' : st === 'pending' ? 'Pendientes' : 'Auditados';
                return (
                  <Pressable
                    key={st}
                    onPress={() => setLocalFilters({ ...localFilters, status: st })}
                    style={[styles.chip, isSelected && styles.chipSelected]}
                  >
                    <Text
                      style={[styles.chipText, isSelected && styles.chipTextSelected]}
                    >
                      {label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            {/* Filter by Stock Level */}
            <Text style={[styles.sectionLabel, { marginTop: 20 }]}>NIVEL DE STOCK</Text>
            <View style={styles.optionsRow}>
              <Pressable
                onPress={() => setLocalFilters({ ...localFilters, criticalOnly: false })}
                style={[styles.chip, !localFilters.criticalOnly && styles.chipSelected]}
              >
                <Text
                  style={[
                    styles.chipText,
                    !localFilters.criticalOnly && styles.chipTextSelected,
                  ]}
                >
                  Todos los niveles
                </Text>
              </Pressable>
              <Pressable
                onPress={() => setLocalFilters({ ...localFilters, criticalOnly: true })}
                style={[styles.chip, localFilters.criticalOnly && styles.chipSelected]}
              >
                <Text
                  style={[
                    styles.chipText,
                    localFilters.criticalOnly && styles.chipTextSelected,
                  ]}
                >
                  ⚠ Stock Crítico (0 uds.)
                </Text>
              </Pressable>
            </View>

            {/* Buttons */}
            <View style={styles.actionsRow}>
              <Pressable onPress={handleReset} style={styles.resetBtn}>
                <Text style={styles.resetBtnText}>Limpiar</Text>
              </Pressable>
              <Pressable onPress={handleApply} style={styles.applyBtn}>
                <Text style={styles.applyBtnText}>Aplicar filtros</Text>
              </Pressable>
            </View>
          </View>
        </SafeAreaView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  sheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  closeBtn: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: 20,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.text.muted,
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  optionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    backgroundColor: '#FFFFFF',
  },
  chipSelected: {
    borderColor: colors.primary[500],
    backgroundColor: colors.primary[50],
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  chipTextSelected: {
    color: colors.primary[600],
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 28,
  },
  resetBtn: {
    flex: 1,
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  resetBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  applyBtn: {
    flex: 2,
    height: 48,
    borderRadius: 12,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
  },
  applyBtnText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
