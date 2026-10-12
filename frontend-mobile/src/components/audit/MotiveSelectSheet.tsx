import React, { useState } from 'react';
import {
  View,
  Text,
  Pressable,
  Modal,
  StyleSheet,
  SafeAreaView,
  FlatList,
} from 'react-native';
import { MOTIVES_CATALOG } from '../../utils/constants';
import { AuditMotive, MobileActionType } from '../../types/audit';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

interface MotiveSelectSheetProps {
  selectedMotiveId?: string | null;
  onSelectMotive: (motive: AuditMotive) => void;
  requiresMotive: boolean;
  actionType: MobileActionType;
  hasError?: boolean;
}

export const MotiveSelectSheet: React.FC<MotiveSelectSheetProps> = ({
  selectedMotiveId,
  onSelectMotive,
  requiresMotive,
  actionType,
  hasError,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Filter motives relevant to the discrepancy action type
  const availableMotives = MOTIVES_CATALOG.filter((m) => {
    if (!m.applicableAction || m.applicableAction === 'All') return true;
    return m.applicableAction === actionType;
  });

  const selectedMotive = MOTIVES_CATALOG.find((m) => m.id === selectedMotiveId);

  return (
    <View style={styles.container}>
      {/* Field Label with Mandatory Asterisk */}
      <View style={styles.labelRow}>
        <Text style={styles.label}>Motivo</Text>
        {requiresMotive && <Text style={styles.asterisk}> *</Text>}
      </View>

      {/* Select Trigger */}
      <Pressable
        onPress={() => setIsOpen(true)}
        style={({ pressed }) => [
          styles.trigger,
          hasError && styles.triggerError,
          pressed && styles.triggerPressed,
        ]}
      >
        <Text
          style={[
            styles.triggerText,
            !selectedMotive && styles.placeholderText,
          ]}
          numberOfLines={1}
        >
          {selectedMotive ? selectedMotive.label : 'Seleccioná un motivo...'}
        </Text>
        <Icon name="chevron-down" size={16} color={colors.text.muted} />
      </Pressable>

      {/* Selection Modal Bottom Sheet */}
      <Modal
        visible={isOpen}
        transparent
        animationType="slide"
        onRequestClose={() => setIsOpen(false)}
      >
        <View style={styles.modalOverlay}>
          <Pressable style={styles.modalBackdrop} onPress={() => setIsOpen(false)} />
          <SafeAreaView style={styles.sheetContent}>
            {/* Sheet Header */}
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>Seleccionar motivo de ajuste</Text>
              <Pressable
                onPress={() => setIsOpen(false)}
                style={styles.closeButton}
                hitSlop={8}
              >
                <Icon name="x" size={18} color={colors.text.secondary} />
              </Pressable>
            </View>

            {/* Motives List */}
            <FlatList
              data={availableMotives}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.listContent}
              renderItem={({ item }) => {
                const isSelected = item.id === selectedMotiveId;
                return (
                  <Pressable
                    onPress={() => {
                      onSelectMotive(item);
                      setIsOpen(false);
                    }}
                    style={({ pressed }) => [
                      styles.motiveItem,
                      isSelected && styles.motiveItemSelected,
                      pressed && styles.motiveItemPressed,
                    ]}
                  >
                    <Text
                      style={[
                        styles.motiveItemText,
                        isSelected && styles.motiveItemTextSelected,
                      ]}
                    >
                      {item.label}
                    </Text>
                    {isSelected && <Icon name="check" size={16} color={colors.primary[500]} />}
                  </Pressable>
                );
              }}
            />
          </SafeAreaView>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  asterisk: {
    fontSize: 12,
    fontWeight: '700',
    color: '#DC2626',
  },
  trigger: {
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
  },
  triggerError: {
    borderColor: '#DC2626',
    backgroundColor: '#FEF2F2',
  },
  triggerPressed: {
    backgroundColor: '#F8FAFC',
  },
  triggerText: {
    fontSize: 14,
    color: colors.text.primary,
    flex: 1,
    paddingRight: 8,
  },
  placeholderText: {
    color: colors.text.disabled,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalBackdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  sheetContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '60%',
    paddingBottom: 20,
  },
  sheetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  sheetTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text.primary,
  },
  closeButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  motiveItem: {
    height: 48,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    marginBottom: 4,
  },
  motiveItemSelected: {
    backgroundColor: colors.primary[50],
  },
  motiveItemPressed: {
    backgroundColor: '#F1F5F9',
  },
  motiveItemText: {
    fontSize: 14,
    color: colors.text.primary,
  },
  motiveItemTextSelected: {
    fontWeight: '700',
    color: colors.primary[600],
  },
});
