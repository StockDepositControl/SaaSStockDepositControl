import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  Pressable,
  TextInput,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

interface BarcodeScannerModalProps {
  isVisible: boolean;
  onClose: () => void;
  onScan: (barcode: string) => void;
}

export const BarcodeScannerModal: React.FC<BarcodeScannerModalProps> = ({
  isVisible,
  onClose,
  onScan,
}) => {
  const [manualCode, setManualCode] = useState('');
  const [isTorchOn, setIsTorchOn] = useState(false);

  const handleSimulate = (code: string) => {
    onScan(code);
    onClose();
  };

  return (
    <Modal visible={isVisible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView style={styles.container}>
        {/* Top Header */}
        <View style={styles.header}>
          <Pressable onPress={onClose} style={styles.headerButton} hitSlop={10}>
            <Icon name="x" size={22} color="#FFFFFF" />
          </Pressable>
          <Text style={styles.headerTitle}>Escáner de código de barras</Text>
          <Pressable
            onPress={() => setIsTorchOn(!isTorchOn)}
            style={styles.headerButton}
            hitSlop={10}
          >
            <Icon
              name="flash"
              size={20}
              color={isTorchOn ? '#FBBF24' : '#FFFFFF'}
            />
          </Pressable>
        </View>

        {/* Viewfinder Area */}
        <View style={styles.viewfinderContainer}>
          <View style={styles.viewfinderBox}>
            <View style={[styles.corner, styles.cornerTL]} />
            <View style={[styles.corner, styles.cornerTR]} />
            <View style={[styles.corner, styles.cornerBL]} />
            <View style={[styles.corner, styles.cornerBR]} />
            <View style={styles.laserLine} />
          </View>
          <Text style={styles.hintText}>
            Alineá el código de barras dentro del marco
          </Text>
        </View>

        {/* Quick Testing Barcodes & Manual Entry */}
        <View style={styles.footer}>
          <Text style={styles.footerLabel}>Simular escaneo de prueba:</Text>
          <View style={styles.sampleRow}>
            <Pressable
              style={styles.samplePill}
              onPress={() => handleSimulate('7798010343227')}
            >
              <Text style={styles.samplePillText}>Ibuprofeno</Text>
            </Pressable>
            <Pressable
              style={styles.samplePill}
              onPress={() => handleSimulate('7798010343228')}
            >
              <Text style={styles.samplePillText}>Paracetamol</Text>
            </Pressable>
            <Pressable
              style={styles.samplePill}
              onPress={() => handleSimulate('7798010343229')}
            >
              <Text style={styles.samplePillText}>Amoxicilina (0)</Text>
            </Pressable>
          </View>

          <View style={styles.manualInputRow}>
            <TextInput
              style={styles.manualInput}
              value={manualCode}
              onChangeText={setManualCode}
              placeholder="Ingresar EAN manualmente..."
              placeholderTextColor="#94A3B8"
              keyboardType="number-pad"
            />
            <Pressable
              style={styles.manualSubmitButton}
              onPress={() => {
                if (manualCode.trim()) {
                  handleSimulate(manualCode.trim());
                }
              }}
            >
              <Text style={styles.manualSubmitText}>OK</Text>
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090D16',
    justifyContent: 'space-between',
  },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  viewfinderContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  viewfinderBox: {
    width: 260,
    height: 180,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  corner: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: '#3B82F6',
  },
  cornerTL: { top: -2, left: -2, borderTopWidth: 4, borderLeftWidth: 4, borderTopLeftRadius: 8 },
  cornerTR: { top: -2, right: -2, borderTopWidth: 4, borderRightWidth: 4, borderTopRightRadius: 8 },
  cornerBL: { bottom: -2, left: -2, borderBottomWidth: 4, borderLeftWidth: 4, borderBottomLeftRadius: 8 },
  cornerBR: { bottom: -2, right: -2, borderBottomWidth: 4, borderRightWidth: 4, borderBottomRightRadius: 8 },
  laserLine: {
    width: '90%',
    height: 2,
    backgroundColor: '#EF4444',
  },
  hintText: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 20,
  },
  footer: {
    padding: 20,
    backgroundColor: '#111827',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  footerLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
    marginBottom: 10,
  },
  sampleRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  samplePill: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  samplePillText: {
    fontSize: 12,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  manualInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  manualInput: {
    flex: 1,
    height: 48,
    backgroundColor: '#1E293B',
    borderRadius: 10,
    paddingHorizontal: 12,
    color: '#FFFFFF',
    fontSize: 14,
  },
  manualSubmitButton: {
    width: 56,
    height: 48,
    backgroundColor: colors.primary[500],
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  manualSubmitText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
