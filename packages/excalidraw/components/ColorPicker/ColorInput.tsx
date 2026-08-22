import clsx from "clsx";
import { useCallback, useEffect, useRef, useState } from "react";

import { KEYS, normalizeInputColor } from "@excalidraw/common";

import { getShortcutKey } from "../..//shortcut";
import { useAtom } from "../../editor-jotai";
import { t } from "../../i18n";
import { useEditorInterface } from "../App";
import { activeEyeDropperAtom } from "../EyeDropper";
import { eyeDropperIcon } from "../icons";

import { activeColorPickerSectionAtom } from "./colorPickerUtils";

import type { ColorPickerType } from "./colorPickerUtils";

const isHexValueValid = (inputValue: string) => {
  const value = inputValue.toLowerCase().trim();

  if (value.length === 0) {
    return true;
  }

  const matchesHexPattern = /^#?([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(
    value,
  );
  const normalizedColor = normalizeInputColor(value);

  return matchesHexPattern && !!normalizedColor;
};

export const ColorInput = ({
  color,
  onChange,
  label,
  colorPickerType,
  placeholder,
}: {
  color: string;
  onChange: (color: string) => void;
  label: string;
  colorPickerType: ColorPickerType;
  placeholder?: string;
}) => {
  const editorInterface = useEditorInterface();
  const [innerValue, setInnerValue] = useState(color);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isValid, setIsValid] = useState(() => isHexValueValid(color || ""));
  const [activeSection, setActiveColorPickerSection] = useAtom(
    activeColorPickerSectionAtom,
  );

  useEffect(() => {
    setInnerValue(color);
  }, [color]);

  const changeColor = useCallback(
    (inputValue: string) => {
      const value = inputValue.toLowerCase().trim();
      const normalizedColor = normalizeInputColor(value);
      const nextIsValid = isHexValueValid(value);

      setIsValid(nextIsValid);

      if (normalizedColor) {
        onChange(normalizedColor);
        setErrorMessage(null);
      } else if (value.length === 0) {
        setErrorMessage(null);
      } else if (/^#?[0-9a-f]+$/.test(value)) {
        setErrorMessage(t("colorPicker.invalidHexLength"));
      } else {
        setErrorMessage(t("colorPicker.invalidColor"));
      }
      setInnerValue(value);
    },
    [onChange],
  );

  const inputRef = useRef<HTMLInputElement>(null);
  const eyeDropperTriggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [activeSection]);

  const [eyeDropperState, setEyeDropperState] = useAtom(activeEyeDropperAtom);

  useEffect(() => {
    return () => {
      setEyeDropperState(null);
    };
  }, [setEyeDropperState]);

  const currentValue = (innerValue || "").replace(/^#/, "");
  const showInvalidState = currentValue.length > 0 && !isValid;

  return (
    <div className="color-picker__input-label-container">
      <div
        className={clsx("color-picker__input-label", {
          "has-error": errorMessage,
        })}
      >
        <div className="color-picker__input-hash">#</div>
        <input
          ref={activeSection === "hex" ? inputRef : undefined}
          style={{
            padding: 0,
            ...(showInvalidState
              ? {
                  border: "1px solid var(--color-danger, #e03131)",
                }
              : { border: 0 }),
          }}
          spellCheck={false}
          className={clsx("color-picker-input", {
            "color-picker-input--invalid": showInvalidState,
          })}
          aria-label={label}
          aria-invalid={showInvalidState || !!errorMessage}
          onChange={(event) => {
            changeColor(event.target.value);
          }}
          value={currentValue}
          onBlur={() => {
            setInnerValue(color);
            setErrorMessage(null);
            setIsValid(isHexValueValid(color || ""));
          }}
          tabIndex={-1}
          onFocus={() => setActiveColorPickerSection("hex")}
          onKeyDown={(event) => {
            if (event.key === KEYS.TAB) {
              return;
            } else if (event.key === KEYS.ESCAPE) {
              eyeDropperTriggerRef.current?.focus();
            }
            event.stopPropagation();
          }}
          placeholder={placeholder}
        />
        {/* TODO reenable on mobile with a better UX */}
        {editorInterface.formFactor !== "phone" && (
          <>
            <div
              style={{
                width: "1px",
                height: "1.25rem",
                backgroundColor: "var(--default-border-color)",
              }}
            />
            <div
              ref={eyeDropperTriggerRef}
              className={clsx("excalidraw-eye-dropper-trigger", {
                selected: eyeDropperState,
              })}
              onClick={() =>
                setEyeDropperState((s) =>
                  s
                    ? null
                    : {
                        keepOpenOnAlt: false,
                        onSelect: (color) => onChange(color),
                        colorPickerType,
                      },
                )
              }
              title={`${t(
                "labels.eyeDropper",
              )} — ${KEYS.I.toLocaleUpperCase()} or ${getShortcutKey("Alt")} `}
            >
              {eyeDropperIcon}
            </div>
          </>
        )}
      </div>
      {showInvalidState && (
        <span
          className="color-input-error"
          style={{
            color: "var(--color-danger, #e03131)",
            fontSize: "11px",
            lineHeight: 1.2,
            marginTop: "2px",
            alignSelf: "flex-start",
            display: "block",
          }}
        >
          Invalid HEX code
        </span>
      )}
      {errorMessage && (
        <div className="color-picker__error-message" role="alert">
          {errorMessage}
        </div>
      )}
    </div>
  );
};
