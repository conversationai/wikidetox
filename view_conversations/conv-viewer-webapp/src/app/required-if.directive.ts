import { Directive,Input,SimpleChanges } from '@angular/core';
import {Validator,AbstractControl} from "@angular/forms";
import {NG_VALIDATORS} from "@angular/forms";

@Directive({
  selector: '[requiredIf]',
   providers: [
     {provide: NG_VALIDATORS,useExisting:RequiredIfDirective, multi: true}
   ]
})
export class RequiredIfDirective implements Validator {
  constructor() { }
  @Input("requiredIf")
  requiredIf: boolean;

  validate(c:AbstractControl) {
    let value = c.value;
     if ((value == null || value == undefined || value == "") && this.requiredIf) {
        return {
            requiredIf: {condition:this.requiredIf}
        };
     }
     return null;
  }

  registerOnValidatorChange(fn: () => void): void { this._onChange = fn; }
  private _onChange: () => void;
  ngOnChanges(changes: SimpleChanges): void {
    if ('requiredIf' in changes) {
      if (this._onChange) this._onChange();
    }
  }
}
